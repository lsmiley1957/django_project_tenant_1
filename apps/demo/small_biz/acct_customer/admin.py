from django.contrib import admin
from apps.demo.small_biz.acct_customer.models import Acct_customer, Stage, SalesProfile


admin.site.register(Acct_customer)


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'description',)
    list_filter = ('name', 'order', 'description',)

@admin.register(SalesProfile)
class SalesProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active_for_leads',)
    list_filter = ('user', 'is_active_for_leads',)