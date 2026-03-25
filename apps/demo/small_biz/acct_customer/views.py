from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.db.models import Count, Sum, DecimalField, F, ExpressionWrapper
from django.db.models.functions import Coalesce

from django.views.decorators.http import require_POST
import json
from django.contrib.auth.models import User
from .models import Acct_customer, CustomerActivity, SalesProfile, CustomerTask, Stage
from apps.demo.small_biz.pos.models import POSTransaction, POSItem
from apps.demo.small_biz.invoicing.models import Invoice, InvoiceItem
from django.db.models import Q, Prefetch

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from datetime import timedelta

from ..inventory.models import Category


@login_required
def crm_dashboard(request):
    """Upgraded Dashboard with Activity Feed"""
    # 1. Pipeline Stats
    stats = Acct_customer.objects.values('status').annotate(total=Count('id'))

    # 2. Stale Leads (No activity in 7 days)
    seven_days_ago = timezone.now() - timedelta(days=7)
    stale_leads = Acct_customer.objects.filter(
        Q(activities__timestamp__lt=seven_days_ago) | Q(activities__isnull=True),
        status__in=['LEAD', 'QUALIFIED']
    ).distinct()

    # 3. Tasks for today
    my_tasks = CustomerTask.objects.filter(
        assigned_to=request.user,
        is_completed=False,
        due_date__date=timezone.now().date()
    )

    # 4. FIX: Fetch Recent Activities for the dashboard feed
    recent_activities = CustomerActivity.objects.select_related('customer', 'user').order_by('-timestamp')[:10]

    return render(request, 'acct_customer/crm_dashboard.html', {
        'pipeline_stats': stats,
        'stale_leads': stale_leads,
        'my_tasks': my_tasks,
        'recent_activities': recent_activities,  # This powers the "Recent Sales Activity" table
    })


@login_required
def pipeline_kanban(request):

    # Get all possible status choices from the model
    stages = Acct_customer.STATUS_CHOICES
    # 1. Get all customers
    # customers = Acct_customer.objects.all()
    customers = Acct_customer.objects.all().prefetch_related('activities').order_by('-id')

    # Structure the data into a list of dictionaries for the template
    # This prevents the need for a 'get_item' dictionary filter
    board_data = []
    for stage_code, stage_name in stages:
        board_data.append({
            'code': stage_code,
            'name': stage_name,
            'customers': [c for c in customers if c.status == stage_code]
        })

    # 2. Apply Search Filter
    q = request.GET.get('q')
    if q:
        customers = customers.filter(name__icontains=q)

    # 3. Apply Sales Rep Filter
    rep_id = request.GET.get('rep')
    if rep_id:
        customers = customers.filter(assigned_to_id=rep_id)

    # 4. Manually define the columns based on your STATUS_CHOICES in models.py
    # This ensures columns show up even if the 'Stage' model isn't working yet
    status_list = [
        ('LEAD', 'New Lead'),
        ('DISCOVERY', 'Discovery'),  # New Column
        ('QUALIFIED', 'Qualified'),
        ('PROPOSAL', 'Proposal Sent'),  # New Column
        ('NEGOTIATION', 'Negotiation'),
        ('WON', 'Won / Onboarding'),  # New Column
        ('ACTIVE', 'Active Client'),
        ('LOST', 'Lost / Archive'),  # New Column
    ]

    board = []
    for status_code, status_name in status_list:
        board.append({
            'name': status_name,
            'status_code': status_code,
            'customers': customers.filter(status=status_code)
        })

    context = {
        'board': board,
        'reps': User.objects.filter(is_staff=True),
    }
    return render(request, 'acct_customer/pipeline_kanban.html', {
        'board_data': board_data,
        'total_count': customers.count(),
    })


@login_required
def customer_activity_json(request, pk):
    try:
        customer = get_object_or_404(Acct_customer, pk=pk)

        # 1. Lifetime Value (POS + Invoices)
        # Sum from POS
        pos_total_data = POSItem.objects.filter(transaction__customer=customer).aggregate(
            total=Coalesce(
                Sum(ExpressionWrapper(F('quantity') * F('unit_price'), output_field=DecimalField())),
                Decimal('0.00')
            ),
            count=Coalesce(Sum('quantity'), 0)
        )

        # Sum from Invoicing (Using total_amount from the Invoice model)
        inv_total_data = Invoice.objects.filter(acct_customer=customer, status='PAID').aggregate(
            total=Coalesce(Sum('total_amount'), Decimal('0.00'))
        )

        # Count items from Invoices
        inv_items_count = InvoiceItem.objects.filter(
            invoice__acct_customer=customer,
            invoice__status='PAID'
        ).aggregate(count=Coalesce(Sum('quantity'), 0))['count'] or 0

        total_value = pos_total_data['total'] + inv_total_data['total']
        total_items = pos_total_data['count'] + inv_items_count

        # 2. Revenue by Category (Combined)
        sales_by_category = []
        pos_cat_data = POSItem.objects.filter(transaction__customer=customer).values(
            'product__category__name'
        ).annotate(
            cat_total=Sum(ExpressionWrapper(F('quantity') * F('unit_price'), output_field=DecimalField()))
        )

        inv_cat_data = InvoiceItem.objects.filter(invoice__acct_customer=customer, invoice__status='PAID').values(
            'product__category__name'
        ).annotate(
            cat_total=Sum('line_total')
        )

        merged_cats = {}
        for item in list(pos_cat_data) + list(inv_cat_data):
            name = item.get('product__category__name') or "General"
            amount = item.get('cat_total') or 0
            merged_cats[name] = merged_cats.get(name, 0) + float(amount)

        for cat, amt in sorted(merged_cats.items(), key=lambda x: x[1], reverse=True):
            if amt > 0:
                sales_by_category.append({'category': cat, 'amount': amt})

        # 3. Activity Log
        activities = CustomerActivity.objects.filter(customer=customer).select_related('user').order_by('-timestamp')[
            :15]
        activity_data = []
        for act in activities:
            activity_data.append({
                'description': act.description,
                'timestamp': act.timestamp.strftime("%b %d, %Y %I:%M %p") if act.timestamp else "No Date",
                'user': act.user.username if act.user else "System"
            })

        # 4. Detailed History for the Pop-out list (Matches the template logic)
        # This part ensures the list of sales in the pop-out actually shows values
        history_list = []

        # Add POS Transactions
        pos_transactions = POSTransaction.objects.filter(customer=customer).order_by('-timestamp')[:5]
        for tx in pos_transactions:
            history_list.append({
                'type': 'POS',
                'receipt': tx.receipt_number,
                'date': tx.timestamp.strftime('%Y-%m-%d'),
                'total': float(tx.total_price),
                'items_count': tx.items.count()
            })

        # Add Paid Invoices
        paid_invoices = Invoice.objects.filter(acct_customer=customer,
                                               status='PAID').order_of_date_issued = Invoice.objects.filter(
            acct_customer=customer, status='PAID').order_by('-date_issued')[:5]
        for inv in paid_invoices:
            history_list.append({
                'type': 'INV',
                'receipt': inv.invoice_number,
                'date': inv.date_issued.strftime('%Y-%m-%d'),
                'total': float(inv.total_amount),
                'items_count': inv.items.count()
            })

        return JsonResponse({
            'status': 'success',
            'total_value': float(total_value),
            'total_items': int(total_items),
            'sales': history_list,  # The list for the History tab
            'category_sales': sales_by_category,  # For charts/summaries
            'activities': activity_data
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)})


def customer_list(request):
    """Lists all acct_customer with search functionality."""
    query = request.GET.get('q')
    if query:
        customers = Acct_customer.objects.filter(
            Q(name__icontains=query) | Q(email__icontains=query)
        )
    else:
        customers = Acct_customer.objects.all()

    return render(request, 'acct_customer/customer_list.html', {'customers': customers})


def add_customer(request):
    """Handles the creation of a new customer."""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')

        Acct_customer.objects.create(
            name=name,
            email=email,
            phone=phone,
            address=address
        )
        return redirect('customer_list')

    return render(request, 'acct_customer/add_customer.html')


def edit_customer(request, pk):
    """Handles updating an existing customer's details."""
    # Fixed: Changed get_object_split to get_object_or_404
    acct_customer = get_object_or_404(Acct_customer, pk=pk)

    if request.method == 'POST':
        acct_customer.name = request.POST.get('name')
        acct_customer.email = request.POST.get('email')
        acct_customer.phone = request.POST.get('phone')
        acct_customer.address = request.POST.get('address')
        acct_customer.save()
        return redirect('customer_list')

    return render(request, 'acct_customer/edit_customer.html', {'acct_customer': acct_customer})


def delete_customer(request, pk):
    """Deletes a customer profile."""
    # Fixed: Changed get_object_split to get_object_or_404
    acct_customer = get_object_or_404(Acct_customer, pk=pk)
    if request.method == 'POST':
        acct_customer.delete()
        return redirect('customer_list')
    return render(request, 'acct_customer/delete_confirm.html', {'acct_customer': acct_customer})


@login_required
def customer_detail(request, pk):
    """
    Detailed Profile view for a customer.
    Aggregates POS sales, Invoices, and Activity.
    """
    customer = get_object_or_404(Acct_customer, pk=pk)

    # 1. Fetch POS Transactions
    pos_transactions = POSTransaction.objects.filter(customer=customer).order_by('-timestamp')
    pos_total = pos_transactions.aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')

    # 2. Fetch Invoices
    invoices = Invoice.objects.filter(acct_customer=customer).order_by('-created_at')
    invoice_total = invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    # 3. Calculate Combined Lifetime Value
    total_revenue = pos_total + invoice_total

    # 4. Aggregated Category Breakdown (POS + Invoicing)
    category_totals = {}

    # 4a. Get POS Category Spending
    pos_items = POSItem.objects.filter(
        transaction__customer=customer
    ).values(
        'product__category__name'
    ).annotate(
        total_spent=Sum(F('quantity') * F('unit_price'))
    )

    for item in pos_items:
        cat_name = item['product__category__name'] or "Uncategorized"
        category_totals[cat_name] = category_totals.get(cat_name, Decimal('0.00')) + (
                    item['total_spent'] or Decimal('0.00'))

    # 4b. Get Invoice Category Spending
    invoice_items = InvoiceItem.objects.filter(
        invoice__acct_customer=customer
    ).values(
        'product__category__name'
    ).annotate(
        total_spent=Sum(F('quantity') * F('sale_price'))
    )

    for item in invoice_items:
        cat_name = item['product__category__name'] or "Uncategorized"
        category_totals[cat_name] = category_totals.get(cat_name, Decimal('0.00')) + (
                    item['total_spent'] or Decimal('0.00'))

    # 4c. Convert to list and calculate percentages
    category_breakdown = []
    if total_revenue > 0:
        # Sort by value descending
        sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)

        for name, spent in sorted_categories:
            percentage = round((spent / total_revenue) * 100, 1)
            category_breakdown.append({
                'name': name,
                'percentage': percentage,
                'total_amount': spent
            })

    # 5. Activity History
    activities = CustomerActivity.objects.filter(customer=customer).order_by('-timestamp')

    context = {
        'customer': customer,
        'pos_transactions': pos_transactions,
        'invoices': invoices,
        'total_revenue': total_revenue,
        'category_breakdown': category_breakdown[:5],  # Top 5 combined categories
        'activities': activities,
    }

    return render(request, 'acct_customer/customer_detail.html', context)

def get_next_salesperson():
    """Round-robin helper to find the next available salesperson"""
    # Orders by the person who hasn't received a lead in the longest time
    profile = SalesProfile.objects.filter(is_active_for_leads=True).order_by('last_assigned_at').first()
    if profile:
        profile.last_assigned_at = timezone.now()
        profile.save()
        return profile.user
    return None


def public_lead_form(request):
    if request.method == 'POST':
        # Extract data from the POST request
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', 'N/A')
        message = request.POST.get('message', '')

        # 1. Determine Lead Assignment
        salesperson = get_next_salesperson()

        # 2. Save to CRM
        # We use update_or_create so that if an old customer returns with a new name/phone,
        # their profile stays current.
        customer, created = Acct_customer.objects.update_or_create(
            email=email,
            defaults={
                'name': name,
                'phone': phone,
                'status': 'LEAD',
                'source': 'Website Form',
                'assigned_to': salesperson
            }
        )

        # 3. Log Activity
        CustomerActivity.objects.create(
            customer=customer,
            description=f"Inquiry received via website form. Message: {message}",
            activity_type='NOTE',
            user=salesperson  # Assign the activity to the salesperson
        )

        # 4. Prepare Email Context
        context = {
            'name': name,
            'email': email,
            'phone': phone,
            'message': message,
            'customer_id': customer.id,
            'assignee_name': salesperson.get_full_name() if salesperson else "Sales Team"
        }

        # --- A. External "Thank You" Email to Customer ---
        thank_you_html = render_to_string('acct_customer/emails/thank_you_lead.html', context)
        send_mail(
            'Thank you for contacting us!',
            strip_tags(thank_you_html),
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=thank_you_html,
            fail_silently=True,
        )

        # --- B. Internal "Sales Alert" Email to Assignee ---
        # If no salesperson is found, send to the general sales email
        recipient_list = [salesperson.email] if salesperson and salesperson.email else [settings.SALES_TEAM_EMAIL]

        alert_html = render_to_string('acct_customer/emails/internal_sales_alert.html', context)
        send_mail(
            f'🔥 New Lead Assigned: {name}',
            strip_tags(alert_html),
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            html_message=alert_html,
            fail_silently=True,
        )

        return render(request, 'acct_customer/lead_success.html', {'name': name})

    return render(request, 'acct_customer/contact_us.html')


@login_required
@require_POST
def update_customer_status(request):
    try:
        data = json.loads(request.body)
        customer_id = data.get('customer_id')
        new_status = data.get('status')

        customer = Acct_customer.objects.get(pk=customer_id)
        old_status = customer.get_status_display()
        customer.status = new_status
        customer.save()

        # Log the change in the activity timeline (Step #2)
        CustomerActivity.objects.create(
            customer=customer,
            user=request.user,
            activity_type='NOTE',
            description=f"Pipeline moved from {old_status} to {customer.get_status_display()}."
        )

        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)