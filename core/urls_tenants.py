from django.contrib import admin
from django.urls import path, include
# from core.views_tenants import DashboardView
from marketplace.views import  MarketplaceView
from django.http import HttpResponse
import logging
from django.conf import settings
from django.conf.urls.static import static


logger = logging.getLogger(__name__)


def middleware_check(request):
    """
    A view that only exists in the tenant URLconf.
    If you can see this, the middleware IS working.
    """
    # Debug info to print in your terminal console
    print(f"DEBUG: Tenant successfully identified as: {request.tenant}")
    return HttpResponse(
        f"<h1>Success!</h1>"
        f"<p>Tenant Name: <b>{request.tenant.name}</b></p>"
        f"<p>Schema Name: <b>{request.tenant.schema_name}</b></p>"
    )


urlpatterns = [
    # 1. Verification Helper
    path('is-tenant/', middleware_check),

    # 2. Admin & Auth
    path('admin/', admin.site.urls),

    # Auth paths (login, logout, etc.)
    path('accounts/', include('django.contrib.auth.urls')),

    # 3. Tenant App Paths
    # path('', DashboardView.as_view(), name='dashboard_home'),
    # path('home/', DashboardView.as_view()),
    path('marketplace/', MarketplaceView.as_view(), name='marketplace'),
    path('branding/', include('apps.demo.small_biz.branding.urls')),

]

# This allows the 'media' folder to be accessible in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)