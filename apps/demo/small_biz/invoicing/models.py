from django.db import models
from django.utils import timezone
from apps.demo.small_biz.inventory.models import Product, StockTransaction
from apps.demo.small_biz.acct_customer.models import Acct_customer


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=20, unique=True)
    acct_customer = models.ForeignKey(Acct_customer, on_delete=models.CASCADE)
    date_issued = models.DateField(default=timezone.now)
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"INV-{self.invoice_number} ({self.acct_customer.name})"

    def mark_as_paid(self):
        if self.status != 'PAID':
            self.status = 'PAID'
            for item in self.items.all():
                StockTransaction.objects.create(
                    product=item.product,
                    change=-item.quantity,
                    type='SALE',
                    notes=f"Invoice {self.invoice_number}"
                )
            self.save()

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    # Updated: Using sale_price to record what the customer was charged
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.sale_price
        super().save(*args, **kwargs)