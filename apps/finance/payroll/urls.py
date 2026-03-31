# payroll/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Employee URLs
    path('employees/', views.EmployeeListView.as_view(), name='employee_list'),
    path('employees/add/', views.EmployeeCreateView.as_view(), name='employee_add'),
    path('employees/<int:pk>/', views.EmployeeDetailView.as_view(), name='employee_detail'),
    path('employees/<int:pk>/edit/', views.EmployeeUpdateView.as_view(), name='employee_edit'),
    path('employees/<int:pk>/delete/', views.EmployeeDeleteView.as_view(), name='employee_delete'),

    # Pay Period URLs
    path('payperiods/', views.PayPeriodListView.as_view(), name='payperiod_list'),
    path('payperiods/add/', views.PayPeriodCreateView.as_view(), name='payperiod_add'),

    # Time Entry URLs
    path('timeentries/add/', views.TimeEntryCreateView.as_view(), name='timeentry_add'),

    # Payroll Processing URL
    path('payroll/process/<int:pay_period_id>/', views.calculate_payroll, name='calculate_payroll'),

    # Payroll Entry List and Detail URLs
    path('payroll/', views.PayrollEntryListView.as_view(), name='payrollentry_list'),
    path('payroll/<int:pk>/', views.PayrollEntryDetailView.as_view(), name='payrollentry_detail'),

    # You might want a homepage or dashboard
    path('', views.EmployeeListView.as_view(), name='home'), # Example: home displays employee list
]

# payroll_project/urls.py
from django.contrib import admin
from django.urls import path, include

