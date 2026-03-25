from django.contrib import admin
from .models import GlobalApp, GlobalDepartment, GlobalRole

@admin.register(GlobalApp)
class GlobalAppAdmin(admin.ModelAdmin):
    """
    Master catalog of applications available to all tenants.
    """
    list_display = ('name', 'system_slug', 'is_premium', 'is_active')
    list_filter = ('is_premium', 'is_active')
    search_fields = ('name', 'system_slug')  # Required for autocomplete
    ordering = ('name',)

@admin.register(GlobalDepartment)
class GlobalDepartmentAdmin(admin.ModelAdmin):
    """
    Standard departments/modules within a Global App.
    """
    list_display = ('name', 'app')
    list_filter = ('app',)
    search_fields = ('name', 'app__name')  # Required for autocomplete
    autocomplete_fields = ['app']

@admin.register(GlobalRole)
class GlobalRoleAdmin(admin.ModelAdmin):
    """
    Standard permission roles within a specific department.
    """
    list_display = ('name', 'get_app', 'department')
    list_filter = ('department__app', 'department')
    search_fields = ('name', 'department__name', 'department__app__name') # FIXES admin.E039
    autocomplete_fields = ['department']

    def get_app(self, obj):
        return obj.department.app
    get_app.short_description = 'Application'
    get_app.admin_order_field = 'department__app'