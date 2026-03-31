# accounting/admin.py
from django.contrib import admin
from django.db.models import Sum
from .models import Account, Contact, Transaction, TransactionLineItem, Invoice, InvoiceItem, Bill, BillItem
from django.core.exceptions import ValidationError

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_type', 'is_active', 'get_balance')
    list_filter = ('account_type', 'is_active')
    search_fields = ('name', 'description')

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_type', 'email', 'phone', 'is_active')
    list_filter = ('contact_type', 'is_active')
    search_fields = ('name', 'email', 'phone')

class TransactionLineItemInline(admin.TabularInline):
    model = TransactionLineItem
    extra = 2 # Number of empty forms to display

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'description', 'reference_number', 'contact', 'status', 'total_debit', 'total_credit')
    list_filter = ('status', 'date', 'contact')
    search_fields = ('description', 'reference_number', 'contact__name')
    inlines = [TransactionLineItemInline]
    date_hierarchy = 'date'

    def total_debit(self, obj):
        return obj.transactionlineitem_set.filter(transaction_type='Debit').aggregate(Sum('amount'))['amount__sum'] or 0
    total_debit.short_description = 'Total Debit'

    def total_credit(self, obj):
        return obj.transactionlineitem_set.filter(transaction_type='Credit').aggregate(Sum('amount'))['amount__sum'] or 0
    total_credit.short_description = 'Total Credit'

    # Override save_model to ensure clean() is called for balancing
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # After saving the transaction, ensure line items are also saved/updated
        # and then re-validate the transaction for balance.
        try:
            obj.clean()
        except ValidationError as e:
            # Add error message to Django admin, potentially redirect to form
            form.add_error(None, e)
            # This is a simplified error handling. For production, you might want to prevent save or revert.


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'invoice_date', 'due_date', 'total_amount', 'amount_paid', 'is_paid', 'transaction')
    list_filter = ('is_paid', 'invoice_date', 'customer')
    search_fields = ('invoice_number', 'customer__name')
    inlines = [InvoiceItemInline]
    date_hierarchy = 'invoice_date'
    readonly_fields = ('total_amount', 'is_paid', 'transaction') # total_amount is calculated

class BillItemInline(admin.TabularInline):
    model = BillItem
    extra = 1

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'vendor', 'bill_date', 'due_date', 'total_amount', 'amount_paid', 'is_paid', 'transaction')
    list_filter = ('is_paid', 'bill_date', 'vendor')
    search_fields = ('bill_number', 'vendor__name')
    inlines = [BillItemInline]
    date_hierarchy = 'bill_date'
    readonly_fields = ('total_amount', 'is_paid', 'transaction') # total_amount is calculated