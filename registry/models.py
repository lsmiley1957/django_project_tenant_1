from django.db import models


class GlobalApp(models.Model):
    """
    The master definition of an application available in the SaaS.
    This lives in the 'public' schema and defines the blueprint for all tenants.
    """
    name = models.CharField(
        max_length=100,
        help_text="Public name of the app (e.g. 'Inventory Pro')"
    )
    system_slug = models.SlugField(
        unique=True,
        help_text="Unique identifier used for routing (e.g. 'inventory-pro')"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed explanation of what the app does for the marketplace."
    )

    # Technical Configuration
    url_conf_path = models.CharField(
        max_length=255,
        help_text="The Python path to the app's URLs, e.g., 'apps.demo.small_biz.inventory.urls'"
    )
    icon_class = models.CharField(
        max_length=50,
        default="fas fa-cube",
        help_text="FontAwesome class for the dashboard icon."
    )

    # Status & Tiering
    is_premium = models.BooleanField(
        default=False,
        help_text="If true, only tenants with premium subscriptions can see/use this."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="If inactive, the app is hidden from all catalogs and dashboards."
    )

    class Meta:
        verbose_name = "Global Application"
        verbose_name_plural = "Global Applications"
        ordering = ['name']

    def __str__(self):
        return self.name


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


class GlobalAppRole(models.Model):
    # Link this role to a specific GlobalApp
    app = models.ForeignKey(GlobalApp, on_delete=models.CASCADE, related_name='roles')
    role_name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('app', 'role_name')

    def __str__(self):
        return f"{self.app.name} - {self.role_name}"


