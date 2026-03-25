from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponseRedirect, JsonResponse
from django.views.generic import TemplateView

from customers.models import Client
from core.views import LandingPageView # Import the class
from customers.views import signup_tenant, signup_success


def check_tenant_exists(request):
    """
    API endpoint to check if a subdomain exists.
    Usage: /check-tenant/?subdomain=acme
    """
    subdomain = request.GET.get('subdomain', '').lower()
    exists = Client.objects.filter(schema_name=subdomain).exists()
    return JsonResponse({'exists': exists})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', LandingPageView.as_view(), name='home'), # Add this line
    path('signup/', signup_tenant, name='signup'),

    # THIS LINE IS CRITICAL TO PREVENT ROLLBACK
    path('signup/success/', signup_success, name='signup_success'),
    path('accounts/', include('django.contrib.auth.urls')),

    # New API endpoint for JavaScript validation
    path('check-tenant/', check_tenant_exists, name='check_tenant'),

    # --- GLOBAL CONTROL SPACE ---
    # Only accessible on the main/public domain
    path('registry-admin/', include('registry.urls')),
    # For now, we define 'dashboard' so the templates don't crash.
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    path('marketplace-control/', include('marketplace.urls')),

]

### Summary of Configuration
# * **Public Site (`localhost:8000`):** Shows the Landing Page with services/blogs and the Signup Form.
# * **Tenant Site (`client.localhost:8000`):** Shows the Dashboard with the tenant's name and plan details.
#
# The files are now logically consistent. Would you like to see how to loop through the `services` and `apps` lists inside your `landing.html` file to display them?