from django.shortcuts import render, redirect, get_object_or_404
from .models import Invoice, InvoiceItem
from apps.demo.small_biz.acct_customer.models import Acct_customer
from apps.demo.small_biz.inventory.models import Product
from django.db import transaction
from django.utils import timezone
import uuid

from django.shortcuts import render, redirect, get_object_or_404
from .models import Invoice, InvoiceItem
from apps.demo.small_biz.acct_customer.models import Acct_customer
from apps.demo.small_biz.inventory.models import Product
from django.db import transaction
from django.utils import timezone
import uuid


def invoice_list(request):
    """Lists all generated invoices."""
    invoices = Invoice.objects.all().order_by('-created_at')
    return render(request, 'invoicing/invoice_list.html', {'invoices': invoices})


def create_invoice(request):
    """
    Handles complex invoice creation.
    Uses sale_price from Product and saves it to InvoiceItem.
    """
    # Consistency: using 'acct_customers' to match the template loop
    customers_list = Acct_customer.objects.all()
    products_list = Product.objects.all()

    if request.method == 'POST':
        acct_customer_id = request.POST.get('acct_customer')
        acct_customer = get_object_or_404(Acct_customer, id=acct_customer_id)
        due_date = request.POST.get('due_date')

        with transaction.atomic():
            invoice_no = uuid.uuid4().hex[:8].upper()

            invoice = Invoice.objects.create(
                invoice_number=invoice_no,
                acct_customer=acct_customer,
                due_date=due_date or timezone.now().date(),
                status='DRAFT'
            )

            product_ids = request.POST.getlist('product_ids[]')
            quantities = request.POST.getlist('quantities[]')

            total_amount = 0
            for p_id, qty in zip(product_ids, quantities):
                if not p_id or not qty:
                    continue

                product = Product.objects.get(id=p_id)
                quantity = int(qty)
                price = product.sale_price
                line_total = price * quantity

                InvoiceItem.objects.create(
                    invoice=invoice,
                    product=product,
                    quantity=quantity,
                    sale_price=price,
                    line_total=line_total
                )
                total_amount += line_total

            invoice.total_amount = total_amount
            invoice.save()

        return redirect('invoice_list')

    return render(request, 'invoicing/create_invoice.html', {
        'acct_customers': customers_list,
        'products': products_list,
        'today': timezone.now()
    })


def edit_invoice(request, pk):
    """View to edit an existing invoice."""
    invoice = get_object_or_404(Invoice, pk=pk)
    customers_list = Acct_customer.objects.all()
    products_list = Product.objects.all()

    if request.method == 'POST':
        try:
            acct_customer_id = request.POST.get('acct_customer')
            due_date = request.POST.get('due_date')
            product_ids = request.POST.getlist('product_ids[]')
            quantities = request.POST.getlist('quantities[]')

            with transaction.atomic():
                # 1. Update basic info
                invoice.acct_customer = get_object_or_404(Acct_customer, id=acct_customer_id)
                invoice.due_date = due_date

                # 2. Clear old items
                invoice.items.all().delete()

                # 3. Re-create items
                total_amount = 0
                for p_id, qty in zip(product_ids, quantities):
                    if not p_id or not qty:
                        continue

                    product = Product.objects.get(id=p_id)
                    quantity = int(qty)
                    price = product.sale_price
                    line_total = price * quantity

                    InvoiceItem.objects.create(
                        invoice=invoice,
                        product=product,
                        quantity=quantity,
                        sale_price=price,
                        line_total=line_total
                    )
                    total_amount += line_total

                invoice.total_amount = total_amount
                invoice.save()

            return redirect('invoice_list')

        except Exception as e:
            print(f"Error updating invoice: {e}")

    # FIXED: context variable name 'acct_customers' now matches customers_list
    return render(request, 'invoicing/edit_invoice.html', {
        'invoice': invoice,
        'acct_customers': customers_list,
        'products': products_list
    })


def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'invoicing/invoice_detail.html', {'invoice': invoice})


def update_invoice_status(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Invoice.STATUS_CHOICES):
            if new_status == 'PAID':
                invoice.mark_as_paid()
            else:
                invoice.status = new_status
                invoice.save()
    return redirect('invoice_detail', pk=pk)