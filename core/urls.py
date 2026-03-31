"""
Primary URL configuration for the project.
This file consolidates routing for both the public landing page and tenant workspaces.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponseRedirect, JsonResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from functools import wraps

from core.views import LandingPageView
# from core.views_tenants import DashboardView
from customers.views import signup_tenant, signup_success
from customers.models import Client
from django.conf import settings
from django.conf.urls.static import static
from apps.demo.small_biz.branding.views import favicon_view # Import the view

def check_tenant_exists(request):
    """
    API endpoint for the Script on the Landing Page.
    """
    subdomain = request.GET.get('subdomain', '').lower()
    exists = Client.objects.filter(schema_name=subdomain).exists()
    return JsonResponse({'exists': exists})

def tenant_only_view(view_func):
    """
    Prevents public schema access to tenant-specific views.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        tenant = getattr(request, 'tenant', None)
        if not tenant or tenant.schema_name == 'public':
            return HttpResponseRedirect('http://localhost:8000/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/profile.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenant'] = self.request.tenant
        return context

urlpatterns = [
    # --- 1. Public & Shared Routes (Main Domain) ---
    path('admin/', admin.site.urls),
    path('', LandingPageView.as_view(), name='home'),
    path('signup/', signup_tenant, name='signup'),
    path('signup/success/', signup_success, name='signup_success'),
    path('check-tenant/', check_tenant_exists, name='check_tenant'),

    # --- 2. Authentication (Tenant Scoped) ---
    path('accounts/', include('django.contrib.auth.urls')),

    # --- 3. Tenant Specific Routes (Protected) ---
    # path('dashboard/', tenant_only_view(DashboardView.as_view()), name='dashboard_home'),

    # path('dashboard/', DashboardView.as_view(), name='dashboard'),

    path('accounts/profile/', tenant_only_view(ProfileView.as_view()), name='profile'),

    # --- 4. Marketplace Application ---
    # We wrap the include to ensure all marketplace activity is within a tenant
    path('marketplace/', include('marketplace.urls')),
    path('chores/', include('chores.urls')),
    path('inventory/', include('apps.demo.small_biz.inventory.urls')),
    path('invoicing/', include('apps.demo.small_biz.invoicing.urls')),
    path('pos/', include('apps.demo.small_biz.pos.urls')),
    path('acct_customer/', include('apps.demo.small_biz.acct_customer.urls')),
    path('favicon.ico', favicon_view),  # Handle the favicon request
    path('branding/', include('apps.demo.small_biz.branding.urls')),
    path('accounting/', include('apps.finance.accounting.urls')),
    path('payroll/', include('apps.finance.payroll.urls')),
    path('crm/', include('apps.operations.crm.urls')),
    path('projects/', include('apps.operations.projects.urls')),
    path('registry', include('registry.urls')),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)