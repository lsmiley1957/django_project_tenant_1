# payroll/forms.py
from django import forms
from .models import Employee, PayPeriod, TimeEntry

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'first_name', 'last_name', 'employee_id', 'email',
            'date_of_hire', 'base_salary', 'hourly_rate', 'is_active',
            'bank_account_number', 'tax_id_number'
        ]
        widgets = {
            'date_of_hire': forms.DateInput(attrs={'type': 'date'}),
        }

class PayPeriodForm(forms.ModelForm):
    class Meta:
        model = PayPeriod
        fields = ['name', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = ['employee', 'pay_period', 'date', 'hours_worked', 'overtime_hours', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
