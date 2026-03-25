from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import Client, Domain


class DomainInline(admin.TabularInline):
    """
    Allows viewing and editing domains directly from the Client (Tenant) page.
    """
    model = Domain
    max_num = 1
    can_delete = False


@admin.register(Client)
class ClientAdmin(TenantAdminMixin, admin.ModelAdmin):
    """
    The main admin interface for Managing Tenants.
    TenantAdminMixin allows you to manage the Domain records
    directly from the Client page.
    """
    # Updated to match the fields in your uploaded models.py
    list_display = ('name', 'schema_name', 'plan', 'on_trial', 'paid_until', 'created_on')
    list_filter = ('plan', 'on_trial', 'created_on')
    search_fields = ('name', 'schema_name')

    # Note: TenantAdminMixin automatically handles Domain inlines
    # if the models are set up correctly.


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """
    A secondary admin for managing Domain records directly.
    Useful for troubleshooting hostname mismatches.
    """
    list_display = ('domain', 'tenant', 'is_primary')
    search_fields = ('domain',)