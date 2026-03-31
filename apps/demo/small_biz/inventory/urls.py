from django.urls import path
from . import views

urlpatterns = [

    path('', views.dashboard, name='dashboard'),

    path('transactions/', views.dashboard, name='transaction_list'),
    # Setup / Seeding URLs
    # 1. The view that renders the setup wizard page
    path('setup/', views.seed_setup, name='seed_setup'), # Add this if missing
    path('setup/seed/', views.initiate_seeding, name='initiate_seeding'),
    path('setup/wizard/', views.seed_setup, name='seed_setup'),
    # 2. The view that processes the POST data to seed the database
    path('setup/initiate/', views.initiate_seeding, name='initiate_seeding'),

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

    # Customer Management
    path('acct_customers/', views.manage_customers, name='manage_customers'),
    # path('macct_customer/<int:pk>/edit/', views.edit_category, name='edit_category'),

    # Supplier Management
    path('manage/suppliers/', views.manage_suppliers, name='manage_suppliers'),
    path('manage/suppliers/<int:pk>/edit/', views.edit_supplier, name='edit_supplier'),

    # Reporting Page and Tabs
    path('reports', views.inventory_reporting, name='inventory_reporting')
]