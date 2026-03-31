from django.db import models
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field

class GlobalApp(models.Model):
    """
    The master definition of an application available in the SaaS.
    RETAINS ALL ORIGINAL FIELDS TO PRESERVE EXISTING DATA.
    """
    # --- YOUR ORIGINAL FIELDS (Keep exactly as in DB) ---
    name = models.CharField(
        max_length=100,
        help_text="Public name of the app (e.g. 'Inventory Pro')"
    )
    system_slug = models.SlugField(
        unique=True,
        help_text="Unique identifier used for routing (e.g. 'inventory-pro')"
    )
    # Note: We keep your original 'description' field
    description = models.TextField(
        blank=True,
        help_text="Detailed explanation of what the app does."
    )
    url_conf_path = models.CharField(
        max_length=255,
        help_text="The Python path to the app's URLs"
    )
    icon_class = models.CharField(
        max_length=50,
        default="fas fa-cube",
        help_text="FontAwesome class for the dashboard icon."
    )
    is_premium = models.BooleanField(
        default=False,
        help_text="If true, only tenants with premium subscriptions can use this."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="If false, this app is hidden from all catalogs."
    )

    # --- NEW ADDITIONS (Safe to add via Migrations) ---
    # Marketing Enhancements
    short_description = models.CharField(max_length=255, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Marketplace Links
    link_url_1 = models.URLField(blank=True, null=True, help_text="e.g. Documentation")
    link_label_1 = models.CharField(max_length=50, blank=True, default="Documentation")
    link_url_2 = models.URLField(blank=True, null=True, help_text="e.g. Support")
    link_label_2 = models.CharField(max_length=50, blank=True, default="Support")

    # Automation
    is_default = models.BooleanField(
        default=False,
        help_text="Automatically install this app for every new tenant."
    )

    class Meta:
        verbose_name = "Global App"
        verbose_name_plural = "Global Apps"
        ordering = ['name']

    def __str__(self):
        return self.name


# Keeping your related structure for Departments and Roles
class GlobalDepartment(models.Model):
    """
    Groups roles within an app (e.g. 'Sales', 'Warehouse', 'Admin').
    Used to organize permissions and UI sections.
    """
    app = models.ForeignKey(
        GlobalApp,
        on_delete=models.CASCADE,
        related_name='departments'
    )
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Global Department"
        verbose_name_plural = "Global Departments"
        ordering = ['name']

    def __str__(self):
        return f"{self.app.name} / {self.name}"


class GlobalRole(models.Model):
    """
    The specific permission level within a department (e.g. 'Manager', 'Viewer').
    This is what is ultimately assigned to individual users.
    """
    department = models.ForeignKey(
        GlobalDepartment,
        on_delete=models.CASCADE,
        related_name='roles'
    )
    name = models.CharField(max_length=100)

    # You might want to add a weight or priority if certain roles are "higher" than others
    # weight = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Global Role"
        verbose_name_plural = "Global Roles"
        ordering = ['department', 'name']

    def __str__(self):
        return f"{self.department.name} -> {self.name}"

    @property
    def app(self):
        """Shortcut to get the parent app from a role instance."""
        return self.department.app


class GlobalAppScreenshot(models.Model):
    """New model for Marketplace visuals."""
    app = models.ForeignKey(GlobalApp, related_name='screenshots', on_delete=models.CASCADE)
    image_url = models.URLField()
    caption = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']







class GlobalAppRole(models.Model):
    # Link this role to a specific GlobalApp
    app = models.ForeignKey(GlobalApp, on_delete=models.CASCADE, related_name='roles')
    role_name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('app', 'role_name')

    def __str__(self):
        return f"{self.app.name} - {self.role_name}"


