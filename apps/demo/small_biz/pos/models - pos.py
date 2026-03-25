from django.db import models

from apps.demo.small_biz.acct_customer.models import Acct_customer
from apps.demo.small_biz.inventory.models import Product, StockTransaction
from django.utils import timezone


# After creating the 'customer' app, you can use this import:
# from customer.models import Customer

class POSSession(models.Model):
    """Tracks a register session (e.g., Morning Shift)."""
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    def __str__(self):
        return f"Session {self.id} ({self.start_time.strftime('%Y-%m-%d')})"


class POSTransaction(models.Model):
    """A single receipt/checkout."""
    session = models.ForeignKey(POSSession, on_delete=models.CASCADE)
    receipt_number = models.CharField(max_length=50, unique=True)

    # Using 'customers.Customer' is the correct lazy-loading syntax
    # to avoid circular dependencies between the sales apps and the customer app.
    # customer = models.ForeignKey('customers.Customer',on_delete=models.SET_NULL,null=True,blank=True,related_name='pos_transactions',help_text="Optional: Link to a customer for loyalty points/history")
    customer = models.ForeignKey(
        'acct_customer.Acct_customer',
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=[('CASH', 'Cash'), ('CARD', 'Card')])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Receipt {self.receipt_number}"


class POSItem(models.Model):
    """Individual items within a POS transaction."""
    transaction = models.ForeignKey(POSTransaction, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.pk:
            # POS transactions deduct stock immediately upon creation
            StockTransaction.objects.create(
                product=self.product,
                change=-self.quantity,
                type='SALE',
                notes=f"POS Sale: {self.transaction.receipt_number}"
            )
        super().save(*args, **kwargs)