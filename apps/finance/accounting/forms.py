# accounting/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Account, Contact, Transaction, TransactionLineItem, Invoice, InvoiceItem, Bill, BillItem

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'account_type', 'description', 'is_active']

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'contact_type', 'email', 'phone', 'address', 'is_active']

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['date', 'description', 'reference_number', 'contact', 'status']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class TransactionLineItemForm(forms.ModelForm):
    class Meta:
        model = TransactionLineItem
        fields = ['account', 'transaction_type', 'amount', 'memo']

# This factory creates a formset for TransactionLineItems related to a Transaction
TransactionLineItemFormSet = inlineformset_factory(
    Transaction,
    TransactionLineItem,
    form=TransactionLineItemForm,
    extra=2, # Number of empty forms to display initially
    can_delete=True
)

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['customer', 'invoice_date', 'due_date', 'invoice_number', 'notes']
        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['description', 'quantity', 'unit_price', 'revenue_account']

InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=1,
    can_delete=True
)

class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['vendor', 'bill_date', 'due_date', 'bill_number', 'notes']
        widgets = {
            'bill_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

class BillItemForm(forms.ModelForm):
    class Meta:
        model = BillItem
        fields = ['description', 'quantity', 'unit_price', 'expense_account']

BillItemFormSet = inlineformset_factory(
    Bill,
    BillItem,
    form=BillItemForm,
    extra=1,
    can_delete=True
)