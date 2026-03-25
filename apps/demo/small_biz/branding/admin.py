from django.contrib import admin
from django.db import connection
from .models import Branding, RegistryApp, AppRole, UserAppAssignment

# --- Branding Admin (Schema-Aware & Singleton) ---

if connection.schema_name != 'public':
    @admin.register(Branding)
    class BrandingAdmin(admin.ModelAdmin):
        """
        Admin configuration for the singleton Branding model.
        Only registered in tenant schemas to prevent public schema crashes.
        """
        list_display = ('company_name', 'city', 'state_province', 'country', 'tax_number')

        fieldsets = (
            ('Brand Identity', {
                'fields': ('company_name', 'logo', 'favicon'),
                'description': "Visual assets used across the tenant's interface."
            }),
            ('Contact Information', {
                'fields': (
                    'address_line_1', 'address_line_2',
                    ('city', 'state_province', 'postal_code'),
                    'country', 'phone_number', 'email_address', 'website_url'
                )
            }),
            ('Financial Defaults', {
                'fields': (('currency_symbol', 'tax_number'), 'default_tax_rate'),
                'classes': ('collapse',),
                'description': "Default settings for invoicing and POS modules."
            }),
        )

        def has_add_permission(self, request):
            # Enforce singleton pattern: only one Branding record allowed per tenant
            if self.model.objects.exists():
                return False
            return super().has_add_permission(request)

# --- Registry & App Management (Always Registered) ---

class AppRoleInline(admin.TabularInline):
    """Allows defining roles directly inside the RegistryApp view."""
    model = AppRole
    extra = 2
    fields = ('role_name', 'description')

@admin.register(RegistryApp)
class RegistryAppAdmin(admin.ModelAdmin):
    """Manages the available software modules in the system."""
    list_display = ('name', 'slug', 'is_active', 'role_count')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [AppRoleInline]

    def role_count(self, obj):
        return obj.roles.count()
    role_count.short_description = "Defined Roles"

@admin.register(AppRole)
class AppRoleAdmin(admin.ModelAdmin):
    """Stand-alone management for roles."""
    list_display = ('role_name', 'app')
    list_filter = ('app',)
    search_fields = ('role_name', 'app__name')

@admin.register(UserAppAssignment)
class UserAppAssignmentAdmin(admin.ModelAdmin):
    """The 'Team Management' view."""
    list_display = ('user', 'global_app', 'get_app', 'app_role', 'assigned_at')
    list_filter = ('app_role', 'assigned_at', 'global_app', 'department')
    search_fields = ('user__username', 'user__email', 'app_role__role_name')
    autocomplete_fields = ['user', 'global_app', 'department', 'app_role']

    def get_app(self, obj):
        return obj.app_role.app.name
    get_app.short_description = 'App'