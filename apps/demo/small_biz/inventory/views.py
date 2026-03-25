from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Product, Category, Supplier, ProductImage, StockTransaction
from django.db import models  # This defines 'models' for models.F
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Count, Q
from django.db.models.functions import Abs # Import Abs function
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json


@login_required
def dashboard(request):
    """Main overview with fixed data aggregation for charts."""
    products = Product.objects.all()
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()

    # Low stock items logic
    low_stock = products.filter(quantity_in_stock__lte=models.F('reorder_level'))

    now = timezone.now()
    timeframes = {
        '24h': now - timedelta(hours=24),
        '7d': now - timedelta(days=7),
        '14d': now - timedelta(days=14),
        '30d': now - timedelta(days=30),
        '90d': now - timedelta(days=90),
        '180d': now - timedelta(days=180),
        '365d': now - timedelta(days=365),
    }

    category_sales_data = {}

    for label, delta in timeframes.items():
        # Querying for 'SALE' or any negative 'change' (which implies stock going out)
        # This covers both explicit 'SALE' types and any manual 'OUT' adjustments
        sales_qs = StockTransaction.objects.filter(
            Q(type__iexact='SALE') | Q(change__lt=0),
            timestamp__gte=delta
        ).values('product__category__name').annotate(
            total_qty=Sum(Abs('change'))
        ).order_by('-total_qty')[:10]

        # Calculate total volume for this specific timeframe to get percentages
        grand_total = sum(item['total_qty'] for item in sales_qs if item['total_qty']) or 0

        formatted_list = []
        for item in sales_qs:
            cat_name = item['product__category__name'] or "Uncategorized"
            val = float(item['total_qty'] or 0)

            # Calculate percentage relative to the top 10 total
            percentage = round((val / float(grand_total)) * 100, 1) if grand_total > 0 else 0

            formatted_list.append({
                'name': cat_name,
                'value': percentage,
                'raw': val
            })

        category_sales_data[label] = formatted_list

    # Activity Feed
    recent_transactions = StockTransaction.objects.select_related('product', 'product__category').order_by(
        '-timestamp')[:10]

    context = {
        'total_products': products.count(),
        'total_categories': categories.count(),
        'total_suppliers': suppliers.count(),
        'low_stock_count': low_stock.count(),
        'recent_transactions': recent_transactions,
        'category_sales_json': json.dumps(category_sales_data),
    }

    return render(request, 'inventory/dashboard.html', context)


@login_required
def inventory_reporting(request):
    """Inventory efficiency and financial analytics."""
    products = Product.objects.all()
    total_inventory_value = sum(p.quantity_in_stock * p.unit_price for p in products)

    # 1. Turnover & DSI (Last 365 Days)
    year_ago = timezone.now() - timedelta(days=365)

    # Cost of Goods Sold (COGS) = Sum of 'OUT' transactions * unit_price
    cogs_data = StockTransaction.objects.filter(
        type='OUT',
        timestamp__gte=year_ago
    ).annotate(
        cost=ExpressionWrapper(Abs(F('change')) * F('product__unit_price'), output_field=DecimalField())
    ).aggregate(total_cogs=Sum('cost'))['total_cogs'] or Decimal('0.00')

    # Average Inventory Value (Simplified: current value)
    avg_inventory = total_inventory_value or Decimal('1.00')
    turnover_ratio = round(cogs_data / avg_inventory, 2)
    dsi = round(365 / turnover_ratio, 1) if turnover_ratio > 0 else 365

    # 2. Dead Stock (No movement in 12 months)
    active_product_ids = StockTransaction.objects.filter(
        timestamp__gte=year_ago
    ).values_list('product_id', flat=True).distinct()

    dead_stock = products.exclude(id__in=active_product_ids)
    dead_stock_count = dead_stock.count()
    dead_stock_value = sum(p.quantity_in_stock * p.unit_price for p in dead_stock)
    dead_stock_pct = round((dead_stock_count / products.count()) * 100, 1) if products.count() > 0 else 0

    context = {
        'turnover_ratio': turnover_ratio,
        'dsi': dsi,
        'dead_stock_count': dead_stock_count,
        'dead_stock_value': dead_stock_value,
        'dead_stock_pct': dead_stock_pct,
        'total_inventory_value': total_inventory_value,
    }
    return render(request, 'inventory/reporting.html', context)

@login_required
def product_list(request):
    """Full catalog view."""
    products = Product.objects.all()
    return render(request, 'inventory/product_list.html', {'products': products})


@login_required
def add_product(request):
    """Initial product creation."""
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()

    if request.method == "POST":
        product = Product.objects.create(
            sku=request.POST.get('sku'),
            name=request.POST.get('name'),
            category_id=request.POST.get('category') or None,
            supplier_id=request.POST.get('supplier') or None,
            sale_price=request.POST.get('sale_price'),
            quantity_in_stock=request.POST.get('quantity_in_stock', 0),
            reorder_level=request.POST.get('reorder_level', 10)
        )
        # Create initial transaction
        StockTransaction.objects.create(
            product=product,
            change=product.quantity_in_stock,
            type='RESTOCK',
            notes="Initial stock entry"
        )
        return redirect('product_list')

    return render(request, 'inventory/add_product.html', {
        'categories': categories,
        'suppliers': suppliers
    })


@login_required
def edit_product(request, pk):
    """
    Advanced Editor: Orchestrates Smart Inventory & Media
    Handles image gallery, stock audit trails, and location/expiry tracking.
    """
    product = get_object_or_404(Product, pk=pk)
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()

    if request.method == "POST":
        # 1. Update Core Information
        product.sku = request.POST.get('sku')
        product.name = request.POST.get('name')
        product.category_id = request.POST.get('category') or None
        product.supplier_id = request.POST.get('supplier') or None

        # Updated to use new pricing fields
        product.cost_price = request.POST.get('cost_price', 0.00)
        product.sale_price = request.POST.get('sale_price', 0.00)

        # Audit Trail: Track manual stock adjustments
        try:
            new_stock = int(request.POST.get('quantity_in_stock', 0))
            if new_stock != product.quantity_in_stock:
                adjustment = new_stock - product.quantity_in_stock
                StockTransaction.objects.create(
                    product=product,
                    change=adjustment,
                    type='ADJUST',
                    notes="Manual adjustment via Pro-Editor"
                )
            product.quantity_in_stock = new_stock
        except ValueError:
            pass  # Handle non-integer input if necessary

        product.reorder_level = request.POST.get('reorder_level', 10)

        # 2. Advanced Tracking: Location & Expiry
        product.location = request.POST.get('location')
        expiry_val = request.POST.get('expiry_date')
        product.expiry_date = expiry_val if expiry_val else None

        # 3. Handle Media Gallery
        # Update Main Image
        if request.FILES.get('main_image'):
            product.main_image = request.FILES.get('main_image')

        # NOTE: If you have a separate ProductImage model for a gallery,
        # ensure those models are imported. For now, we update the core product fields.

        product.save()
        return redirect('product_list')

    # Calculate safe metrics for the template to avoid AttributeErrors
    # If these methods don't exist on your model yet, we provide safe defaults
    sales_velocity = getattr(product, 'sales_velocity', 0)
    days_cover = getattr(product, 'days_of_cover', 'N/A')

    return render(request, 'inventory/edit_product.html', {
        'product': product,
        'categories': categories,
        'suppliers': suppliers,
        'sales_velocity': sales_velocity,
        'days_cover': days_cover
    })


@login_required
def update_stock(request, pk):
    """Quick adjustment view for rapid stock-taking/sales."""
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        adjustment = int(request.POST.get('adjustment', 0))
        product.quantity_in_stock += adjustment
        product.save()

        # Record specific transaction type
        t_type = 'SALE' if adjustment < 0 else 'RESTOCK'
        StockTransaction.objects.create(
            product=product,
            change=adjustment,
            type=t_type,
            notes="Dashboard quick-adjustment"
        )
        return redirect('dashboard')
    return render(request, 'inventory/update_stock.html', {'product': product})


@login_required
def manage_categories(request):
    if request.method == "POST":
        Category.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description')
        )
        return redirect('manage_categories')
    categories = Category.objects.all()
    return render(request, 'inventory/manage_categories.html', {'categories': categories})


@login_required
def manage_suppliers(request):
    if request.method == "POST":
        Supplier.objects.create(
            name=request.POST.get('name'),
            contact_email=request.POST.get('email'),
            phone=request.POST.get('phone')
        )
        return redirect('manage_suppliers')
    suppliers = Supplier.objects.all()
    return render(request, 'inventory/manage_suppliers.html', {'suppliers': suppliers})


@login_required
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')
        category.save()
        return redirect('manage_categories')
    return render(request, 'inventory/edit_category.html', {'category': category})


@login_required
def edit_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == "POST":
        supplier.name = request.POST.get('name')
        supplier.contact_email = request.POST.get('email')
        supplier.phone = request.POST.get('phone')
        supplier.save()
        return redirect('manage_suppliers')
    return render(request, 'inventory/edit_supplier.html', {'supplier': supplier})