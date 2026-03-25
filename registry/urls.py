from django.urls import path
from . import views

app_name = 'registry'

urlpatterns = [
    # This matches /registry/ exactly
    path('', views.GlobalAppListView.as_view(), name='app_list'),

    # Existing app paths
    path('apps/', views.GlobalAppListView.as_view(), name='app_list_alt'),
    path('apps/add/', views.GlobalAppCreateView.as_view(), name='app_add'),
    path('apps/<int:pk>/', views.GlobalAppDetailView.as_view(), name='app_detail'),

    # NEW: Edit Route
    path('apps/<int:pk>/edit/', views.GlobalAppUpdateView.as_view(), name='app_edit'),

    # Management paths
    path('apps/<int:app_id>/add-dept/', views.add_department, name='add_dept'),
    path('apps/<int:app_id>/clone/', views.clone_app_structure, name='app_clone'),
    path('dept/<int:dept_id>/add-role/', views.quick_add_role, name='add_role_ajax'),

    # API/Manifest
    path('manifest/', views.get_registry_manifest, name='manifest'),



]