# accounting/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone

class Account(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('Asset', 'Asset'),
        ('Liability', 'Liability'),
        ('Equity', 'Equity'),
        ('Revenue', 'Revenue'),
        ('Expense', 'Expense'),
        ('Contra-Asset', 'Contra-Asset'), # e.g., Accumulated Depreciation
        ('Contra-Liability', 'Contra-Liability'), # e.g., Discount on Bonds Payable
        ('Contra-Equity', 'Contra-Equity'), # e.g., Dividends
        ('Contra-Revenue', 'Contra-Revenue'), # e.g., Sales Returns and Allowances
        ('Contra-Expense', 'Contra-Expense'), # e.g., Purchase Returns and Allowances
    ]

    name = models.CharField(max_length=200, unique=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.account_type})"

    def get_balance(self):
        """Calculates the current balance of the account."""
        debits = self.transactionlineitem_set.filter(transaction_type='Debit').aggregate(Sum('amount'))['amount__sum'] or 0
        credits = self.transactionlineitem_set.filter(transaction_type='Credit').aggregate(Sum('amount'))['amount__sum'] or 0

        if self.account_type in ['Asset', 'Expense', 'Contra-Liability', 'Contra-Equity', 'Contra-Revenue']:
            return debits - credits
        else: # Liability, Equity, Revenue, Contra-Asset, Contra-Expense
            return credits - debits

class Contact(models.Model):
    CONTACT_TYPE_CHOICES = [
        ('Customer', 'Customer'),
        ('Vendor', 'Vendor'),
        ('Both', 'Both'),
    ]
    name = models.CharField(max_length=200)
    contact_type = models.CharField(max_length=10, choices=CONTACT_TYPE_CHOICES)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.contact_type})"

class Transaction(models.Model):
    TRANSACTION_STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Posted', 'Posted'),
        ('Void', 'Void'),
    ]
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255)
    reference_number = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Invoice #, Check #")
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUS_CHOICES, default='Draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"Transaction on {self.date} - {self.description}"

    def clean(self):
        """Ensures that debits and credits balance for a transaction."""
        super().clean()
        if self.pk: # Only validate if transaction exists (i.e., being updated or has line items)
            total_debits = self.transactionlineitem_set.filter(transaction_type='Debit').aggregate(Sum('amount'))['amount__sum'] or 0
            total_credits = self.transactionlineitem_set.filter(transaction_type='Credit').aggregate(Sum('amount'))['amount__sum'] or 0

            if total_debits != total_credits:
                raise ValidationError("Total debits must equal total credits for this transaction.")

    def save(self, *args, **kwargs):
        self.full_clean() # Call full_clean to run clean() method before saving
        super().save(*args, **kwargs)

class TransactionLineItem(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('Debit', 'Debit'),
        ('Credit', 'Credit'),
    ]
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.PROTECT) # PROTECT to prevent deleting account if it has entries
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    memo = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['transaction', 'id'] # Order by ID to maintain entry order

    def __str__(self):
        return f"{self.transaction.description} - {self.account.name}: {self.transaction_type} ${self.amount}"

    def clean(self):
        """Ensures amount is positive."""
        if self.amount <= 0:
            raise ValidationError({'amount': 'Amount must be positive.'})

class Invoice(models.Model):
    customer = models.ForeignKey(Contact, on_delete=models.PROTECT, limit_choices_to={'contact_type__in': ['Customer', 'Both']})
    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    invoice_number = models.CharField(max_length=50, unique=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_paid = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    # Link to a transaction if this invoice is posted to the ledger
    transaction = models.OneToOneField(Transaction, on_delete=models.SET_NULL, null=True, blank=True, help_text="Journal entry for this invoice")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-invoice_date', '-invoice_number']

    def __str__(self):
        return f"Invoice #{self.invoice_number} for {self.customer.name}"

    def save(self, *args, **kwargs):
        self.total_amount = sum(item.amount for item in self.invoiceitem_set.all())
        self.is_paid = self.amount_paid >= self.total_amount and self.total_amount > 0
        super().save(*args, **kwargs)

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False) # Calculated field
    # Link to a revenue account (e.g., Sales Revenue)
    revenue_account = models.ForeignKey(Account, on_delete=models.PROTECT, limit_choices_to={'account_type': 'Revenue'})

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.description} on Invoice #{self.invoice.invoice_number}"

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        # Update parent invoice total
        self.invoice.save() # Recalculate total_amount on parent invoice

class Bill(models.Model):
    vendor = models.ForeignKey(Contact, on_delete=models.PROTECT, limit_choices_to={'contact_type__in': ['Vendor', 'Both']})
    bill_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    bill_number = models.CharField(max_length=50, unique=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_paid = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    # Link to a transaction if this bill is posted to the ledger
    transaction = models.OneToOneField(Transaction, on_delete=models.SET_NULL, null=True, blank=True, help_text="Journal entry for this bill")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-bill_date', '-bill_number']

    def __str__(self):
        return f"Bill #{self.bill_number} from {self.vendor.name}"

    def save(self, *args, **kwargs):
        self.total_amount = sum(item.amount for item in self.billitem_set.all())
        self.is_paid = self.amount_paid >= self.total_amount and self.total_amount > 0
        super().save(*args, **kwargs)

class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False) # Calculated field
    # Link to an expense account (e.g., Office Supplies Expense)
    expense_account = models.ForeignKey(Account, on_delete=models.PROTECT, limit_choices_to={'account_type': 'Expense'})

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.description} on Bill #{self.bill.bill_number}"

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        # Update parent bill total
        self.bill.save() # Recalculate total_amount on parent bill
