from django.urls import path
from . import views

app_name = 'pos'
urlpatterns = [
    path('', views.pos_interface, name='pos_terminal'),
    path('process/', views.process_sale, name='pos_process'),

    # POS Terminal Routes
    path('pos/', views.pos_terminal, name='pos_terminal'),
    path('pos/checkout/', views.pos_checkout, name='pos_checkout'),

    # History & Receipts

    path('transactions/', views.transaction_list, name='transaction_list'),
    path('receipt/<int:pk>/', views.receipt_detail, name='pos_receipt_detail'),

]
