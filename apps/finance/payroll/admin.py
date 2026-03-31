# payroll/admin.py
from django.contrib import admin
from .models import Employee, PayPeriod, TimeEntry, DeductionType, EmployeeDeduction, PayrollEntry

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'employee_id', 'email', 'is_active', 'date_of_hire')
    search_fields = ('first_name', 'last_name', 'employee_id', 'email')
    list_filter = ('is_active', 'date_of_hire')

@admin.register(PayPeriod)
class PayPeriodAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date')
    list_filter = ('start_date', 'end_date')

@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'hours_worked', 'overtime_hours', 'pay_period')
    list_filter = ('employee', 'pay_period', 'date')
    search_fields = ('employee__first_name', 'employee__last_name')

@admin.register(DeductionType)
class DeductionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_tax_deduction')

@admin.register(EmployeeDeduction)
class EmployeeDeductionAdmin(admin.ModelAdmin):
    list_display = ('employee', 'deduction_type', 'amount', 'is_active')
    list_filter = ('employee', 'deduction_type', 'is_active')

@admin.register(PayrollEntry)
class PayrollEntryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'pay_period', 'gross_pay', 'total_deductions', 'net_pay', 'payment_date', 'status')
    list_filter = ('pay_period', 'status', 'payment_date')
    search_fields = ('employee__first_name', 'employee__last_name')
    date_hierarchy = 'payment_date'
