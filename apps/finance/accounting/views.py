# accounting/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction as db_transaction # Avoid conflict with model name
from django.forms import formset_factory
from django.forms import inlineformset_factory
from django.db.models import Sum
from decimal import Decimal
from django.core.exceptions import ValidationError

from .models import Account, Contact, Transaction, TransactionLineItem, Invoice, InvoiceItem, Bill, BillItem
from .forms import (
    AccountForm, ContactForm, TransactionForm, TransactionLineItemFormSet,
    InvoiceForm, InvoiceItemFormSet, BillForm, BillItemFormSet, InvoiceItemForm
)

# --- Account Views ---
class AccountListView(LoginRequiredMixin, ListView):
    model = Account
    template_name = 'accounting/account_list.html'
    context_object_name = 'accounts'

class AccountDetailView(LoginRequiredMixin, DetailView):
    model = Account
    template_name = 'accounting/account_detail.html'
    context_object_name = 'account'

class AccountCreateView(LoginRequiredMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = 'accounting/account_form.html'
    success_url = reverse_lazy('account_list')

class AccountUpdateView(LoginRequiredMixin, UpdateView):
    model = Account
    form_class = AccountForm
    template_name = 'accounting/account_form.html'
    success_url = reverse_lazy('account_list')

class AccountDeleteView(LoginRequiredMixin, DeleteView):
    model = Account
    template_name = 'accounting/account_confirm_delete.html'
    success_url = reverse_lazy('account_list')

# --- Contact Views ---
class ContactListView(LoginRequiredMixin, ListView):
    model = Contact
    template_name = 'accounting/contact_list.html'
    context_object_name = 'contacts'

class ContactDetailView(LoginRequiredMixin, DetailView):
    model = Contact
    template_name = 'accounting/contact_detail.html'
    context_object_name = 'contact'

class ContactCreateView(LoginRequiredMixin, CreateView):
    model = Contact
    form_class = ContactForm
    template_name = 'accounting/contact_form.html'
    success_url = reverse_lazy('contact_list')

class ContactUpdateView(LoginRequiredMixin, UpdateView):
    model = Contact
    form_class = ContactForm
    template_name = 'accounting/contact_form.html'
    success_url = reverse_lazy('contact_list')

class ContactDeleteView(LoginRequiredMixin, DeleteView):
    model = Contact
    template_name = 'accounting/contact_confirm_delete.html'
    success_url = reverse_lazy('contact_list')

# --- Transaction Views (with inline formset for line items) ---
class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'accounting/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 10

class TransactionDetailView(LoginRequiredMixin, DetailView):
    model = Transaction
    template_name = 'accounting/transaction_detail.html'
    context_object_name = 'transaction'

def transaction_create_update_view(request, pk=None):
    if not request.user.is_authenticated:
        return redirect('login') # Assuming you have a login URL

    transaction_instance = None
    if pk:
        transaction_instance = get_object_or_404(Transaction, pk=pk)

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction_instance)
        formset = TransactionLineItemFormSet(request.POST, instance=transaction_instance)

        if form.is_valid() and formset.is_valid():
            with db_transaction.atomic():
                transaction = form.save()
                formset.instance = transaction # Link formset to the saved transaction
                formset.save()

                # Re-run clean method on the transaction to ensure balance after line items are saved
                try:
                    transaction.clean()
                    transaction.save() # Save again if clean() made changes or to re-trigger signals
                except ValidationError as e:
                    # If balance is off, delete the transaction and its line items, then show error
                    transaction.delete() # This will cascade delete line items
                    form.add_error(None, f"Transaction failed to balance: {e.message}")
                    return render(request, 'accounting/transaction_form.html', {
                        'form': form,
                        'formset': formset,
                        'is_update': pk is not None
                    })

            return redirect('transaction_list')
    else:
        form = TransactionForm(instance=transaction_instance)
        formset = TransactionLineItemFormSet(instance=transaction_instance)

    return render(request, 'accounting/transaction_form.html', {
        'form': form,
        'formset': formset,
        'is_update': pk is not None
    })

class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = 'accounting/transaction_confirm_delete.html'
    success_url = reverse_lazy('transaction_list')

# --- Invoice Views (with inline formset for invoice items) ---
class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'accounting/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 10

class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'accounting/invoice_detail.html'
    context_object_name = 'invoice'

def invoice_create_update_view(request, pk=None):
    if not request.user.is_authenticated:
        return redirect('login')

    invoice_instance = None
    if pk:
        invoice_instance = get_object_or_404(Invoice, pk=pk)

    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice_instance)
        formset = InvoiceItemFormSet(request.POST, instance=invoice_instance)

        # if form.is_valid() and formset.is_valid():
        #     with db_transaction.atomic():
        #         invoice = form.save(commit=False) # Don't save yet, need to calculate total_amount
        #         invoice.save() # Save the invoice first to get an ID for items
        #         formset.instance = invoice
        #         formset.save()
        #
        #         # Recalculate total_amount and save again after items are saved
        #         invoice.save()

        if request.method == 'POST':
            form = InvoiceForm(request.POST, instance=invoice_instance)
            formset = InvoiceItemFormSet(request.POST, instance=invoice_instance)

            if form.is_valid() and formset.is_valid():
                with db_transaction.atomic():
                    invoice = form.save(commit=False)  # Don't save yet
                    invoice.save()  # Save the invoice first to get an ID
                    formset.instance = invoice
                    formset.save()
                    invoice.save()  # Recalculate total_amount

            return redirect('invoice_list')
    else:
        form = InvoiceForm(instance=invoice_instance)
        formset = InvoiceItemFormSet(instance=invoice_instance)

    return render(request, 'accounting/invoice_form.html', {
        'form': form,
        'formset': formset,
        'is_update': pk is not None
    })


def post_invoice_to_ledger(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')

    invoice = get_object_or_404(Invoice, pk=pk)

    if invoice.transaction:
        # Invoice already posted, maybe show a message or redirect
        return redirect('invoice_detail', pk=pk) # Or show error message

    # Basic double-entry for an invoice:
    # Debit Accounts Receivable (Asset)
    # Credit Sales Revenue (Revenue)
    try:
        accounts_receivable = Account.objects.get(name='Accounts Receivable', account_type='Asset')
        sales_revenue = Account.objects.get(name='Sales Revenue', account_type='Revenue')
        # You might need more specific revenue accounts based on invoice items
    except Account.DoesNotExist:
        # Handle error: required accounts not found
        # You might want to create them if they don't exist, or redirect with an error message
        return render(request, 'accounting/error_page.html', {'message': 'Required accounting accounts (Accounts Receivable, Sales Revenue) not found. Please create them in the admin.'})

    with db_transaction.atomic():
        transaction = Transaction.objects.create(
            date=invoice.invoice_date,
            description=f"Invoice #{invoice.invoice_number} for {invoice.customer.name}",
            reference_number=invoice.invoice_number,
            contact=invoice.customer,
            status='Posted'
        )

        TransactionLineItem.objects.create(
            transaction=transaction,
            account=accounts_receivable,
            transaction_type='Debit',
            amount=invoice.total_amount
        )
        TransactionLineItem.objects.create(
            transaction=transaction,
            account=sales_revenue,
            transaction_type='Credit',
            amount=invoice.total_amount
        )
        # You might need to iterate through InvoiceItems and credit specific revenue accounts
        # For simplicity, we're crediting a single Sales Revenue account for the total.

        invoice.transaction = transaction
        invoice.save()

    return redirect('invoice_detail', pk=pk)


# --- Bill Views (with inline formset for bill items) ---
class BillListView(LoginRequiredMixin, ListView):
    model = Bill
    template_name = 'accounting/bill_list.html'
    context_object_name = 'bills'
    paginate_by = 10

class BillDetailView(LoginRequiredMixin, DetailView):
    model = Bill
    template_name = 'accounting/bill_detail.html'
    context_object_name = 'bill'

def bill_create_update_view(request, pk=None):
    if not request.user.is_authenticated:
        return redirect('login')

    bill_instance = None
    if pk:
        bill_instance = get_object_or_404(Bill, pk=pk)

    if request.method == 'POST':
        form = BillForm(request.POST, instance=bill_instance)
        formset = BillItemFormSet(request.POST, instance=bill_instance)

        if form.is_valid() and formset.is_valid():
            with db_transaction.atomic():
                bill = form.save(commit=False)
                bill.save()
                formset.instance = bill
                formset.save()

                bill.save() # Recalculate total_amount

            return redirect('bill_list')
    else:
        form = BillForm(instance=bill_instance)
        formset = BillItemFormSet(instance=bill_instance)

    return render(request, 'accounting/bill_form.html', {
        'form': form,
        'formset': formset,
        'is_update': pk is not None
    })

def post_bill_to_ledger(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')

    bill = get_object_or_404(Bill, pk=pk)

    if bill.transaction:
        return redirect('bill_detail', pk=pk)

    # Basic double-entry for a bill:
    # Debit Expense Account (e.g., Office Supplies Expense)
    # Credit Accounts Payable (Liability)
    try:
        accounts_payable = Account.objects.get(name='Accounts Payable', account_type='Liability')
        # For simplicity, we'll use a generic expense account or the one from the first item
        # In a real app, you'd iterate through bill items and debit their respective expense accounts
        # For this example, we'll assume the first item's expense account is representative.
        # OR, you'd have a default "Miscellaneous Expense"
        default_expense_account = Account.objects.filter(account_type='Expense').first()
        if not default_expense_account:
             return render(request, 'accounting/error_page.html', {'message': 'No Expense account found. Please create one in the admin.'})

    except Account.DoesNotExist:
        return render(request, 'accounting/error_page.html', {'message': 'Required accounting accounts (Accounts Payable, Expense) not found. Please create them in the admin.'})


    with db_transaction.atomic():
        transaction = Transaction.objects.create(
            date=bill.bill_date,
            description=f"Bill #{bill.bill_number} from {bill.vendor.name}",
            reference_number=bill.bill_number,
            contact=bill.vendor,
            status='Posted'
        )

        # Debit the expense account(s)
        for item in bill.billitem_set.all():
            TransactionLineItem.objects.create(
                transaction=transaction,
                account=item.expense_account, # Use the specific expense account from the bill item
                transaction_type='Debit',
                amount=item.amount
            )

        # Credit Accounts Payable for the total bill amount
        TransactionLineItem.objects.create(
            transaction=transaction,
            account=accounts_payable,
            transaction_type='Credit',
            amount=bill.total_amount
        )

        bill.transaction = transaction
        bill.save()

    return redirect('bill_detail', pk=pk)


# --- Reporting Views ---
class TrialBalanceView(LoginRequiredMixin, TemplateView):
    template_name = 'accounting/trial_balance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        accounts = Account.objects.filter(is_active=True).order_by('name')

        trial_balance_data = []
        total_debits = Decimal('0.00')
        total_credits = Decimal('0.00')

        for account in accounts:
            balance = account.get_balance()
            debit_balance = Decimal('0.00')
            credit_balance = Decimal('0.00')

            if account.account_type in ['Asset', 'Expense', 'Contra-Liability', 'Contra-Equity', 'Contra-Revenue']:
                if balance >= 0:
                    debit_balance = balance
                else:
                    credit_balance = abs(balance) # Negative asset/expense is a credit
            else: # Liability, Equity, Revenue, Contra-Asset, Contra-Expense
                if balance >= 0:
                    credit_balance = balance
                else:
                    debit_balance = abs(balance) # Negative liability/equity/revenue is a debit

            trial_balance_data.append({
                'account': account,
                'debit_balance': debit_balance,
                'credit_balance': credit_balance,
            })
            total_debits += debit_balance
            total_credits += credit_balance

        context['trial_balance_data'] = trial_balance_data
        context['total_debits'] = total_debits
        context['total_credits'] = total_credits
        return context

class IncomeStatementView(LoginRequiredMixin, TemplateView):
    template_name = 'accounting/income_statement.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # You might want to add date range filtering here
        # For simplicity, this calculates for all time or a default period.
        # A real income statement needs a specific period (e.g., month, quarter, year).

        revenue_accounts = Account.objects.filter(account_type__in=['Revenue', 'Contra-Revenue'], is_active=True)
        expense_accounts = Account.objects.filter(account_type__in=['Expense', 'Contra-Expense'], is_active=True)

        total_revenue = Decimal('0.00')
        revenue_details = []
        for account in revenue_accounts:
            # For income statement, we need the sum of credits for revenue accounts
            # and sum of debits for contra-revenue accounts for the period.
            # This simplified version just uses get_balance which is cumulative.
            # A proper report needs to filter transactions by date.
            # Example:
            # period_credits = account.transactionlineitem_set.filter(
            #     transaction_type='Credit', transaction__date__range=[start_date, end_date]
            # ).aggregate(Sum('amount'))['amount__sum'] or 0
            # period_debits = account.transactionlineitem_set.filter(
            #     transaction_type='Debit', transaction__date__range=[start_date, end_date]
            # ).aggregate(Sum('amount'))['amount__sum'] or 0

            # For now, using get_balance for simplicity, but note it's cumulative.
            balance = account.get_balance()
            revenue_details.append({'account': account, 'balance': balance})
            total_revenue += balance

        total_expense = Decimal('0.00')
        expense_details = []
        for account in expense_accounts:
            balance = account.get_balance()
            expense_details.append({'account': account, 'balance': balance})
            total_expense += balance

        net_income = total_revenue - total_expense

        context['revenue_details'] = revenue_details
        context['total_revenue'] = total_revenue
        context['expense_details'] = expense_details
        context['total_expense'] = total_expense
        context['net_income'] = net_income
        return context


# --- Main Dashboard / Home View ---
class AccountingDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounting/base.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_transactions'] = Transaction.objects.all()[:5]
        context['recent_invoices'] = Invoice.objects.all()[:5]
        context['recent_bills'] = Bill.objects.all()[:5]
        return context