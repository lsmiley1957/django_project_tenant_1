from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
import os


# --- Helper Functions for File Storage ---

def product_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"main.{ext}"
    return os.path.join('products', str(instance.sku), filename)


def gallery_image_path(instance, filename):
    return os.path.join('products', str(instance.product.sku), 'gallery', filename)


# --- Core Inventory Models ---

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    average_lead_time = models.FloatField(default=3.5)
    reliability_rate = models.FloatField(default=98.0)
    defect_rate = models.FloatField(default=0.5)

    def __str__(self):
        return self.name


class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)

    # Cost Price: What we pay (Utilizing your unit_price as Cost)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Our buying price")

    # Sale Price: What the customer pays (For POS and Invoicing)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,
                                     help_text="Price charged to acct_customer")

    quantity_in_stock = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=10)
    location = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    date_added = models.DateTimeField(default=timezone.now)
    main_image = models.ImageField(upload_to=product_image_path, blank=True, null=True)

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.quantity_in_stock <= self.reorder_level

    @property
    def profit_margin(self):
        """Calculates profit per unit."""
        return self.sale_price - self.cost_price

    @property
    def margin_percentage(self):
        if self.sale_price > 0:
            return (self.profit_margin / self.sale_price) * 100
        return 0


class ProductImage(models.Model):
    """Gallery images for the multi-image product editor."""
    product = models.ForeignKey(Product, related_name='gallery_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to=gallery_image_path)
    created_at = models.DateTimeField(auto_now_add=True)


class StockTransaction(models.Model):
    """The engine that tracks every stock movement and updates Product totals."""
    TRANSACTION_TYPES = [
        ('SALE', 'Sale'),
        ('RESTOCK', 'Restock'),
        ('ADJUST', 'Manual Adjustment'),
        ('RETURN', 'Return/Defect'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    change = models.IntegerField(help_text="Positive for restock, negative for sales")
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default='ADJUST')
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        # Only update the product stock level if this is a new transaction
        if not self.pk:
            self.product.quantity_in_stock += self.change
            self.product.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} | {self.change} ({self.type}) @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"