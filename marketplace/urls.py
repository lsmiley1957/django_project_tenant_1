from django.urls import path
from .views import (
    DashboardView,
    MarketplaceView,
    AppDetailView,
    AppManagementListView,
    AppCreateUpdateView
)

urlpatterns = [
    # --- 1. Workspace Hub (Tenant Dashboard) ---
    path('dashboard/', DashboardView.as_view(), name='dashboard_home'),

    # --- 2. Public-facing Marketplace Browser ---
    path('', MarketplaceView.as_view(), name='marketplace'),
    path('app/<slug:slug>/', AppDetailView.as_view(), name='app_detail'),

    # --- 3. Admin Management Routes (CRUD) ---
    # App Management
    path('manage/', AppManagementListView.as_view(), name='marketplace_admin_list'),
    path('manage/apps/', AppManagementListView.as_view(), name='tenant_app_manager'),

    # Billing & Usage Placeholder
    # (Pointing to Dashboard for now to prevent NoReverseMatch)
    path('manage/billing/', DashboardView.as_view(), name='billing_manager'),

    # Software Center Placeholder
    path('manage/software/', DashboardView.as_view(), name='software_center'),

    # CRUD operations
    path('manage/create/', AppCreateUpdateView.as_view(), name='app_create'),
    path('manage/edit/<slug:slug>/', AppCreateUpdateView.as_view(), name='app_edit'),
]