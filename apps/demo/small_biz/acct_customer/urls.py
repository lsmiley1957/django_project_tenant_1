from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.crm_dashboard, name='crm_dashboard'),
    path('pipeline/', views.pipeline_kanban, name='pipeline_kanban'), # New entry
    path('', views.customer_list, name='customer_list'),
    path('add/', views.add_customer, name='add_customer'),
    path('<int:pk>/edit/', views.edit_customer, name='edit_customer'),
    path('<int:pk>/delete/', views.delete_customer, name='delete_customer'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('contact-us/', views.public_lead_form, name='contact_us'),
    path('update-status/', views.update_customer_status, name='update_customer_status'),
    path('customers/<int:pk>/activity-json/', views.customer_activity_json, name='customer_activity_json'),
    # path('customer-detail/<int:pk>/detail/', views.customer_detail, name='customer_detail'),
]