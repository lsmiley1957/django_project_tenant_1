from django.db import models
# from ckeditor.fields import RichTextField
from django_ckeditor_5.fields import CKEditor5Field



class App(models.Model):
    """The central registry for all available software in the ecosystem."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon_tag = models.CharField(max_length=50, default="box", help_text="Lucide icon name")
    short_description = models.CharField(max_length=255)
    full_description = models.TextField()
    is_active = models.BooleanField(default=True)

    # New Fields: External Links
    link_url_1 = models.URLField(blank=True, null=True, help_text="External URL 1 (e.g. Documentation)")
    link_label_1 = models.CharField(max_length=50, blank=True, null=True, default="Documentation")
    link_url_2 = models.URLField(blank=True, null=True, help_text="External URL 2 (e.g. Support)")
    link_label_2 = models.CharField(max_length=50, blank=True, null=True, default="Support")

    # Track which tenants (Clients) have activated this app
    assigned_tenants = models.ManyToManyField(
        'customers.Client',
        related_name='installed_apps',
        blank=True
    )

    def __str__(self):
        return self.name

class AppTier(models.Model):
    app = models.ForeignKey(App, related_name='tiers', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    setup_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    billing_cycle = models.CharField(max_length=20, default="month") # month, year, one-time
    is_subscription = models.BooleanField(default=True)
    paypal_plan_id = models.CharField(max_length=100, blank=True, help_text="PayPal Subscription Plan ID")
    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.app.name} - {self.name}"


class AppFeature(models.Model):
    app = models.ForeignKey(App, related_name='features', on_delete=models.CASCADE)
    feature_text = models.CharField(max_length=255)

    def __str__(self):
        return self.feature_text


class AppScreenshot(models.Model):
    MEDIA_TYPES = (
        ('image', 'Image'),
        ('video', 'Video'),
    )
    app = models.ForeignKey(App, related_name='screenshots', on_delete=models.CASCADE)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, default='image')
    image_url = models.URLField(help_text="Direct URL to image or Video ID")
    caption = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percent = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} ({self.discount_percent}%)"

class KBArticle(models.Model):
    app = models.ForeignKey(App, related_name='kb_articles', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = CKEditor5Field(config_name='default')
    category = models.CharField(max_length=50, default="General")

    def __str__(self):
        return self.title

class AppRole(models.Model):
    """Global definitions of roles available for an app."""
    app = models.ForeignKey(App, related_name='roles', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.app.name} - {self.name}"