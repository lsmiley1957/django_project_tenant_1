from django.urls import path
from . import views

urlpatterns = [
    path('', views.invoice_list, name='invoice_list'),
    path('new/', views.create_invoice, name='create_invoice'),
    path('<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('<int:pk>/edit/', views.edit_invoice, name='edit_invoice'),  # New edit path
    path('<int:pk>/status/', views.update_invoice_status, name='update_invoice_status'),
]