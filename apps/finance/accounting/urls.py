# accounting/urls.py
from django.urls import path
from . import views

app_name = 'accounting'

urlpatterns = [
    # Dashboard/Home
    path('', views.AccountingDashboardView.as_view(), name='accounting_dashboard'),

    # Account URLs
    path('accounts/', views.AccountListView.as_view(), name='account_list'),
    path('accounts/add/', views.AccountCreateView.as_view(), name='account_add'),
    path('accounts/<int:pk>/', views.AccountDetailView.as_view(), name='account_detail'),
    path('accounts/<int:pk>/edit/', views.AccountUpdateView.as_view(), name='account_edit'),
    path('accounts/<int:pk>/delete/', views.AccountDeleteView.as_view(), name='account_delete'),

    # Contact URLs
    path('contacts/', views.ContactListView.as_view(), name='contact_list'),
    path('contacts/add/', views.ContactCreateView.as_view(), name='contact_add'),
    path('contacts/<int:pk>/', views.ContactDetailView.as_view(), name='contact_detail'),
    path('contacts/<int:pk>/edit/', views.ContactUpdateView.as_view(), name='contact_edit'),
    path('contacts/<int:pk>/delete/', views.ContactDeleteView.as_view(), name='contact_delete'),

    # Transaction URLs
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/add/', views.transaction_create_update_view, name='transaction_add'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('transactions/<int:pk>/edit/', views.transaction_create_update_view, name='transaction_edit'),
    path('transactions/<int:pk>/delete/', views.TransactionDeleteView.as_view(), name='transaction_delete'),

    # Invoice URLs
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/add/', views.invoice_create_update_view, name='invoice_add'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.invoice_create_update_view, name='invoice_edit'),
    path('invoices/<int:pk>/post/', views.post_invoice_to_ledger, name='invoice_post_to_ledger'),

    # Bill URLs
    path('bills/', views.BillListView.as_view(), name='bill_list'),
    path('bills/add/', views.bill_create_update_view, name='bill_add'),
    path('bills/<int:pk>/', views.BillDetailView.as_view(), name='bill_detail'),
    path('bills/<int:pk>/edit/', views.bill_create_update_view, name='bill_edit'),
    path('bills/<int:pk>/post/', views.post_bill_to_ledger, name='bill_post_to_ledger'),

    # Reporting URLs
    path('reports/trial-balance/', views.TrialBalanceView.as_view(), name='trial_balance'),
    path('reports/income-statement/', views.IncomeStatementView.as_view(), name='income_statement'),
]