import json
import uuid
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone

from apps.demo.small_biz.inventory.models import Product
from apps.demo.small_biz.acct_customer.models import Acct_customer, CustomerActivity
from .models import POSSession, POSTransaction, POSItem

@login_required
def pos_terminal(request):
    """
    The main terminal for the Point of Sale.
    Displays all available products.
    """
    products = Product.objects.all()
    acct_customers = Acct_customer.objects.all()

    # Get or create an active session for the terminal
    session = POSSession.objects.filter(end_time__isnull=True).first()
    if not session:
        session = POSSession.objects.create(opening_balance=0.00)

    return render(request, 'pos/terminal.html', {
        'products': products,
        'acct_customers': acct_customers,
        'session': session
    })

@login_required
def pos_checkout(request):
    """
    Processes the sale, creates the transaction, and updates stock.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart = data.get('cart', [])
            customer_id = data.get('acct_customer_id') or data.get('customer_id')
            payment_method = data.get('payment_method', 'CASH')

            if not cart:
                return JsonResponse({'status': 'error', 'message': 'Cart is empty'}, status=400)

            # Get active session
            session = POSSession.objects.filter(end_time__isnull=True).first()
            if not session:
                return JsonResponse({'status': 'error', 'message': 'No active POS session found'}, status=400)

            # Look up customer if ID is provided
            customer_obj = None
            if customer_id:
                try:
                    customer_obj = Acct_customer.objects.get(id=customer_id)
                except Acct_customer.DoesNotExist:
                    customer_obj = None

            with transaction.atomic():
                receipt_no = f"RCPT-{uuid.uuid4().hex[:8].upper()}"

                # Create the transaction - Fixed field name to 'customer'
                transaction_obj = POSTransaction.objects.create(
                    session=session,
                    receipt_number=receipt_no,
                    customer=customer_obj,
                    payment_method=payment_method,
                    total_price=0
                )

                total_amount = 0
                for item in cart:
                    product = Product.objects.get(id=item['id'])
                    qty = int(item['quantity'])
                    unit_price = product.sale_price

                    POSItem.objects.create(
                        transaction=transaction_obj,
                        product=product,
                        quantity=qty,
                        unit_price=unit_price
                    )
                    total_amount += (unit_price * qty)

                # Update header total
                transaction_obj.total_price = total_amount
                transaction_obj.save()

            # Log activity if a customer was attached
            if customer_obj:
                CustomerActivity.objects.create(
                    customer=customer_obj,
                    user=request.user,
                    activity_type='SALE',
                    description=f"Completed purchase: {receipt_no}. Total: ${total_amount}"
                )

            return JsonResponse({
                'status': 'success',
                'receipt_number': receipt_no,
                'redirect_url': '/pos/transactions/',
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=405)

@login_required
def transaction_list(request):
    transactions = POSTransaction.objects.all().order_by('-timestamp')
    return render(request, 'pos/transaction_list.html', {'transactions': transactions})

@login_required
def receipt_detail(request, pk):
    transaction_obj = get_object_or_404(POSTransaction, pk=pk)
    return render(request, 'pos/receipt_detail.html', {'transaction': transaction_obj})

# Aliases for URL routing consistency
pos_interface = pos_terminal
process_sale = pos_checkout

