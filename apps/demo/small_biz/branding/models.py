from django.db import models
from django.db import connection
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

from registry.models import GlobalRole, GlobalDepartment, GlobalApp


def tenant_directory_path(instance, filename):
    """Generates tenant-isolated paths for media files."""
    schema = connection.schema_name
    return f'tenants/{schema}/branding/{filename}'


class Branding(models.Model):
    """
    Tenant-specific branding configuration.
    This model lives in the tenant schema.
    """
    company_name = models.CharField(max_length=255, default="Your Company Name")

    # Using the isolation helper for logo and favicon
    logo = models.ImageField(upload_to=tenant_directory_path, null=True, blank=True)
    favicon = models.ImageField(upload_to=tenant_directory_path, null=True, blank=True)

    # Contact Information
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default="United States")

    phone_number = models.CharField(max_length=50, blank=True)
    email_address = models.EmailField(blank=True)
    website_url = models.URLField(blank=True)
    tax_number = models.CharField(max_length=100, blank=True)

    # Financial Constants
    default_tax_rate = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=0.000,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    currency_symbol = models.CharField(max_length=10, default="$")

    class Meta:
        verbose_name = "Company Branding"
        verbose_name_plural = "Company Branding"

    def __str__(self):
        return f"Branding for {self.company_name} ({connection.schema_name})"


class RegistryApp(models.Model):
    """
    A registry of available internal 'Apps' like 'Inventory', 'Invoicing', 'POS'
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon_class = models.CharField(max_length=50, default="fas fa-cube", help_text="FontAwesome class")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class AppRole(models.Model):
    """
    Specific roles available for an app.
    e.g., 'Cashier' for POS app, 'Stock Clerk' for Inventory app.
    """
    app = models.ForeignKey(RegistryApp, on_delete=models.CASCADE, related_name="roles")
    role_name = models.CharField(max_length=100)
    permissions_description = models.TextField(blank=True)

    class Meta:
        unique_together = ('app', 'role_name')

    def __str__(self):
        return f"{self.app.name} - {self.role_name}"


class UserAppAssignment(models.Model):
    """
    Connects a User to a specific App, and now specifically
    to a Department and Role defined in the Global Registry.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='branding_app_assignments')

    global_app = models.ForeignKey('registry.GlobalApp', on_delete=models.CASCADE)  # The new field

    # NEW: Linking to the Registry's Department and Role
    department = models.ForeignKey(
        GlobalDepartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_assignments'
    )
    app_role = models.ForeignKey(
        GlobalRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_assignments'
    )

    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # FIXED: Changed 'app' to 'global_app' to match the field definition
        unique_together = ('user', 'global_app')
        verbose_name = "User App Assignment"
        verbose_name_plural = "User App Assignments"

    def __str__(self):
        # FIXED: Changed self.app.name to self.global_app.name
        app_name = self.global_app.name if self.global_app else "Unknown App"
        role_name = self.app_role.name if self.app_role else "No Role"
        return f"{self.user.username} - {app_name} ({role_name})"