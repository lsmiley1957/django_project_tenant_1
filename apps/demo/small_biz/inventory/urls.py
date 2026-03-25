from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),  # New URL
    path('products/<int:pk>/update/', views.update_stock, name='update_stock'),

    # Full Product Editing (Update all fields like SKU, Name, Category, etc.)
    path('products/<int:pk>/edit/', views.edit_product, name='edit_product'),

    # Quick Stock Adjustment (The original narrow update function)
    path('products/<int:pk>/update-stock/', views.update_stock, name='update_stock'),

    # Category Management
    path('manage/categories/', views.manage_categories, name='manage_categories'),
    path('manage/categories/<int:pk>/edit/', views.edit_category, name='edit_category'),

    # Supplier Management
    path('manage/suppliers/', views.manage_suppliers, name='manage_suppliers'),
    path('manage/suppliers/<int:pk>/edit/', views.edit_supplier, name='edit_supplier'),

    # Reporting Page and Tabs
    path('reports', views.inventory_reporting, name='inventory_reporting')
]