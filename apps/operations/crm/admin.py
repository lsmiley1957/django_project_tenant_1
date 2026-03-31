# crm_project/crm/admin.py

from django.contrib import admin
from .models import Territory, Lead, Opportunity

# Register your models here to make them visible in the Django admin interface.

@admin.register(Territory)
class TerritoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('created_at',)

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'company', 'source', 'status', 'assigned_to', 'territory', 'created_at')
    list_filter = ('source', 'status', 'assigned_to', 'territory', 'created_at')
    search_fields = ('name', 'email', 'phone', 'company')
    raw_id_fields = ('assigned_to', 'territory') # Use raw ID fields for foreign keys for better performance with many users/territories

@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'lead', 'amount', 'stage', 'close_date', 'assigned_to', 'territory', 'created_at')
    list_filter = ('stage', 'assigned_to', 'territory', 'created_at')
    search_fields = ('name', 'lead__name') # Search by opportunity name or associated lead name
    raw_id_fields = ('lead', 'assigned_to', 'territory') # Use raw ID fields for foreign keys
