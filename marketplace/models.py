from django.db import models

class App(models.Model):
    """The central registry for all available software in the ecosystem."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon_tag = models.CharField(max_length=50, default="box", help_text="Lucide icon name")
    short_description = models.CharField(max_length=255)
    full_description = models.TextField()
    is_active = models.BooleanField(default=True)

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
    billing_cycle = models.CharField(max_length=20, default="month")
    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.app.name} - {self.name}"

class AppFeature(models.Model):
    app = models.ForeignKey(App, related_name='features', on_delete=models.CASCADE)
    feature_text = models.CharField(max_length=255)

    def __str__(self):
        return self.feature_text

class AppScreenshot(models.Model):
    app = models.ForeignKey(App, related_name='screenshots', on_delete=models.CASCADE)
    image_url = models.URLField(help_text="Placeholder URL for screenshots")
    caption = models.CharField(max_length=100, blank=True)

class KBArticle(models.Model):
    app = models.ForeignKey(App, related_name='kb_articles', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=50, default="General")

class AppRole(models.Model):
    """
    Global definitions of roles available for an app.
    Example: Inventory App might have 'Stock Clerk' and 'Warehouse Manager'.
    """
    app = models.ForeignKey(App, related_name='available_roles', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.app.name}: {self.name}"