from django.urls import path
from django.views.generic import TemplateView
from . import views
from .views import TeamManagementView

app_name = 'branding'

urlpatterns = [
    # --- Existing Core Routes ---

    # The Tenant Dashboard (Root of branding)
    path('', views.branding_dashboard, name='branding_dashboard'),

    # Route to manage company information, logo, and currency settings
    path('settings/', views.manage_branding, name='manage_branding'),

    # User Roles Management
    path('users/<int:user_id>/roles/', views.manage_user_roles, name='manage_user_roles'),

    # The User/Team Management UI (Modern view)
    path('manage/team/', TeamManagementView.as_view(), name='manage_team'),

    # Favicon Utility
    path('favicon.ico', views.favicon_view),

    # --- NEW: Marketplace Routes (Option B) ---

    # Browse the Global Registry from within the Tenant
    path('marketplace/', views.marketplace, name='marketplace'),

    # Action to 'Install' a global app to this specific user/tenant
    path('marketplace/install/<int:app_id>/', views.install_app, name='install_app'),

# --- Placeholders ---
# path('dashboard/', TemplateView.as_view(template_name='project_dashboard.html'), name='dashboard')

]