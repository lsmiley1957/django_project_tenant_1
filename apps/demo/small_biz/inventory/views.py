import os
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Category, Supplier, ProductImage, StockTransaction
from django.db import models  # This defines 'models' for models.F
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Count, Q, Value, Avg
from django.db.models.functions import Abs, Coalesce  # Import Abs function
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json
import random

from .seeder import TenantDataSeeder


@login_required
def seed_setup(request):
    """
    Renders the setup wizard selection page (seed_setup.html or setup_wizard.html).
    """
    return render(request, 'inventory/seed_setup.html')


# --- PROCESSING VIEW ---
@login_required
def initiate_seeding(request):
    """
    Handles the POST request from the wizard to populate the database.
    """
    if request.method == "POST":
        # 1. Get the business type from the form
        business_type = request.POST.get('business_type', '').strip().lower()

        if not business_type:
            messages.error(request, "Selection required: Please choose a business type.")
            return redirect('seed_setup')

        # 2. Define supported types (must match keys in your wizard HTML)
        # Note: seeder_2.py handles the filename mapping internally
        supported_types = ['bakery',
                           'electronics',
                           'retail',
                           'pharmacy',
                           'hardware',
                           'grocery',
                           'departmentstore',
                           'sporting']

        if business_type not in supported_types:
            messages.error(request, f"Configuration for '{business_type}' is not supported.")
            return redirect('seed_setup')

        try:
            # 3. Initialize with the business_type string
            # TenantDataSeeder.__init__ expects 'business_type'
            seeder = TenantDataSeeder(business_type)

            # 4. Execute the seeding process
            # TenantDataSeeder.run() handles file pathing and DB insertion
            success = seeder.run()

            if success:
                messages.success(request, f"Successfully deployed {business_type.title()} profile!")
                return redirect('dashboard')
            else:
                messages.error(request,
                               f"Seeding failed: Check if {business_type}_seed.json exists in inventory/data_seeds/")
                return redirect('seed_setup')

        except Exception as e:
            # This catches errors like the AttributeError you were likely hitting
            messages.error(request, f"Seeding error: {str(e)}")
            return redirect('seed_setup')

    # If accessed via GET, just go to the setup page[cite: 7]
    return redirect('seed_setup')
# ... rest of your existing views (inventory_dashboard, etc.)

from django.db.models import Sum, Avg, F, Value, DecimalField, Count, Case, When
from django.db.models.functions import Coalesce, Abs
import json

@login_required
def dashboard(request):
    products = Product.objects.all()

    # --- Top Metrics ---
    total_products = products.count()
    total_categories = Category.objects.count()
    total_suppliers = Supplier.objects.count()
    total_stock_value = sum(p.quantity_in_stock * p.cost_price for p in products)

    # --- Enhanced Stock Distribution (Including Sales Count) ---
    category_dist = Category.objects.annotate(
        item_count=Sum('product__quantity_in_stock'),
        stock_value=Sum(F('product__quantity_in_stock') * F('product__cost_price')),
        avg_unit_cost=Avg('product__cost_price'),
        # New: Calculate total units sold (negative changes in StockTransaction)
        sales_count=Coalesce(
            Sum(
                Case(
                    When(product__stocktransaction__change__lt=0,
                         then=Abs(F('product__stocktransaction__change'))),
                    default=0
                )
            ), 0
        ),
        display_name=Coalesce('name', Value('Uncategorized'))
    ).filter(item_count__gt=0).order_by('-item_count')[:8]

    # --- Sales Breakdown (Bar Chart Logic) ---
    CHART_COLORS = ['#5e72e4', '#2dce89', '#11cdef', '#fb6340', '#f5365c', '#8965e0', '#ffd600', '#2bffc6']
    now = timezone.now()
    timeframes = {'24h': 1, '7d': 7, '30d': 30, '365d': 365}

    category_sales_data = {}
    for label, days in timeframes.items():
        delta = now - timedelta(days=days)
        sales_qs = StockTransaction.objects.filter(
            change__lt=0,
            timestamp__gte=delta
        ).values('product__category__name').annotate(
            rev=Sum(Abs(F('change')) * F('product__sale_price'), output_field=DecimalField()),
            cost=Sum(Abs(F('change')) * F('product__cost_price'), output_field=DecimalField()),
        ).order_by('-rev')[:10]

        total_rev = sum(item['rev'] for item in sales_qs) or Decimal('1')

        formatted_list = []
        for i, item in enumerate(sales_qs):
            revenue = float(item['rev'])
            cost = float(item['cost'])
            margin = round(((revenue - cost) / revenue) * 100, 1) if revenue > 0 else 0

            formatted_list.append({
                'name': item['product__category__name'] or "Uncategorized",
                'value': round((revenue / float(total_rev)) * 100, 1),
                'margin': margin,
                'color': CHART_COLORS[i % len(CHART_COLORS)]
            })
        category_sales_data[label] = formatted_list

    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_suppliers': total_suppliers,
        'total_stock_value': f"{total_stock_value:,.2f}",
        'category_distribution': category_dist,
        'category_sales_json': json.dumps(category_sales_data),
        'dist_labels': json.dumps([c.display_name for c in category_dist]),
        'dist_counts_json': json.dumps([int(c.item_count or 0) for c in category_dist]),
        'dist_values_json': json.dumps([float(c.stock_value or 0) for c in category_dist]),
        'recent_transactions': StockTransaction.objects.select_related('product').order_by('-timestamp')[:10]
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


    products = Product.objects.all().order_by('name')

    # 2. Get the search term 'q' from the URL
    query = request.GET.get('q')

    # 3. If a search term exists, filter the list
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query)
        )

    return render(request, 'inventory/product_list.html', {'products': products})


@login_required
def add_product(request):
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()

    if request.method == "POST":
        # 1. Capture the intended initial stock
        initial_qty = int(request.POST.get('quantity_in_stock', 0))

        # 2. Create the product with 0 stock
        product = Product.objects.create(
            sku=request.POST.get('sku'),
            name=request.POST.get('name'),
            category_id=request.POST.get('category') or None,
            supplier_id=request.POST.get('supplier') or None,
            cost_price=request.POST.get('cost_price', 0.00),
            sale_price=request.POST.get('sale_price', 0.00),
            quantity_in_stock=0,  # Start at zero
            reorder_level=request.POST.get('reorder_level', 10)
        )

        # 3. Create the transaction (this will update Product to initial_qty)
        StockTransaction.objects.create(
            product=product,
            change=initial_qty,
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
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        # Match 'transaction_type' to the name attribute in your HTML <select>
        quantity = int(request.POST.get('quantity', 0))
        transaction_type = request.POST.get('transaction_type') # Changed from 'type'
        notes = request.POST.get('notes')

        if transaction_type:
            StockTransaction.objects.create(
                product=product,
                change=quantity,
                type=transaction_type,
                notes=notes
            )
            messages.success(request, f"Stock updated for {product.name}")
            return redirect('product_list')
        else:
            messages.error(request, "Please select a transaction type.")

    return render(request, 'inventory/update_stock.html', {'product': product})

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

def manage_customers(request):
    if request.method == "POST":
        Category.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description')
        )
        return redirect('manage_customers')
    categories = Category.objects.all()
    return render(request, 'acct_customer:customer_list.html', {'categories': categories})


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