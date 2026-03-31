from django.urls import path
from . import views
from django.contrib.auth import views as auth_views # Import Django's built-in auth views

app_name = 'crm' # Define app namespace for URL reversing

urlpatterns = [
    # Authentication URLs (Django's built-in)
    path('login/', auth_views.LoginView.as_view(template_name='crm/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='crm:login'), name='logout'),

    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Lead URLs
    path('leads/', views.LeadListView.as_view(), name='lead_list'),
    path('leads/new/', views.LeadCreateView.as_view(), name='lead_form'),
    path('leads/<int:pk>/', views.LeadDetailView.as_view(), name='lead_detail'),
    path('leads/<int:pk>/edit/', views.LeadUpdateView.as_view(), name='lead_edit'),
    path('leads/<int:pk>/delete/', views.LeadDeleteView.as_view(), name='lead_delete'),

    # Opportunity URLs
    path('opportunities/', views.OpportunityListView.as_view(), name='opportunity_list'),
    path('opportunities/new/', views.OpportunityCreateView.as_view(), name='opportunity_create'),
    path('opportunities/<int:pk>/', views.OpportunityDetailView.as_view(), name='opportunity_detail'),
    path('opportunities/<int:pk>/edit/', views.OpportunityUpdateView.as_view(), name='opportunity_edit'),
    path('opportunities/<int:pk>/delete/', views.OpportunityDeleteView.as_view(), name='opportunity_delete'),

    # Territory URLS
    path('territories/', views.TerritoryListView.as_view(), name='territory_list'),
    path('territories/new/', views.LeadCreateView.as_view(), name='territory_form'),
    path('territories/<int:pk>/', views.LeadDetailView.as_view(), name='territory_detail'),
    path('territories/<int:pk>/edit/', views.LeadUpdateView.as_view(), name='territory_edit'),
    path('territories/<int:pk>/delete/', views.LeadDeleteView.as_view(), name='territory_delete'),

]