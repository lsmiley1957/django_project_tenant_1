# payroll/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Sum
from .models import Employee, PayPeriod, TimeEntry, EmployeeDeduction, PayrollEntry, DeductionType
from .forms import EmployeeForm, PayPeriodForm, TimeEntryForm
from django.contrib.auth.mixins import LoginRequiredMixin # For authentication

# --- Employee Views ---
class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'payroll/employee_list.html'
    context_object_name = 'employees'

class EmployeeDetailView(LoginRequiredMixin, DetailView):
    model = Employee
    template_name = 'payroll/employee_detail.html'
    context_object_name = 'employee'

class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'payroll/employee_form.html'
    success_url = reverse_lazy('employee_list')

class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'payroll/employee_form.html'
    success_url = reverse_lazy('employee_list')

class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    model = Employee
    template_name = 'payroll/employee_confirm_delete.html'
    success_url = reverse_lazy('employee_list')

# --- PayPeriod Views ---
class PayPeriodListView(LoginRequiredMixin, ListView):
    model = PayPeriod
    template_name = 'payroll/payperiod_list.html'
    context_object_name = 'pay_periods'

class PayPeriodCreateView(LoginRequiredMixin, CreateView):
    model = PayPeriod
    form_class = PayPeriodForm
    template_name = 'payroll/payperiod_form.html'
    success_url = reverse_lazy('payperiod_list')

# --- TimeEntry Views ---
class TimeEntryCreateView(LoginRequiredMixin, CreateView):
    model = TimeEntry
    form_class = TimeEntryForm
    template_name = 'payroll/timeentry_form.html'
    success_url = reverse_lazy('employee_list') # Redirect to employee list or time entry list


# --- Payroll Processing Logic (Simplified) ---
# def calculate_payroll(request, pay_period_id):
#     if not request.user.is_authenticated:
#         return redirect('login') # Assuming you have a login URL
#
#     pay_period = get_object_or_404(PayPeriod, pk=pay_period_id)
#     employees = Employee.objects.filter(is_active=True)
#     processed_count = 0
#
#     for employee in employees:
#         # Check if payroll already exists for this employee and pay period
#         if PayrollEntry.objects.filter(employee=employee, pay_period=pay_period).exists():
#             continue # Skip if already processed
#
#         total_hours = TimeEntry.objects.filter(
#             employee=employee,
#             pay_period=pay_period
#         ).aggregate(Sum('hours_worked'))['hours_worked__sum'] or 0
#
#         total_overtime_hours = TimeEntry.objects.filter(
#             employee=employee,
#             pay_period=pay_period
#         ).aggregate(Sum('overtime_hours'))['overtime_hours__sum'] or 0
#
#         gross_pay = 0.0
#
#         if employee.hourly_rate:
#             # Assuming standard hours are paid at hourly_rate, overtime at 1.5x
#             gross_pay = (float(total_hours) * float(employee.hourly_rate)) + \
#                         (float(total_overtime_hours) * float(employee.hourly_rate) * 1.5)
#         elif employee.base_salary:
#             # Simple division for salaried employees for a bi-weekly period (26 pay periods per year)
#             # You'd need more sophisticated logic for monthly, semi-monthly, etc.
#             gross_pay = float(employee.base_salary) / 26 # Example for bi-weekly
#
#         # Calculate total deductions
#         total_deductions = EmployeeDeduction.objects.filter(
#             employee=employee,
#             is_active=True
#         ).aggregate(Sum('amount'))['amount__sum'] or 0
#
#         net_pay = gross_pay - float(total_deductions)
#
#         PayrollEntry.objects.create(
#             employee=employee,
#             pay_period=pay_period,
#             gross_pay=round(gross_pay, 2),
#             total_deductions=round(float(total_deductions), 2),
#             net_pay=round(net_pay, 2),
#             payment_date=pay_period.end_date, # Or a separate payment date field
#             status='processed'
#         )
#         processed_count += 1
#
#     return render(request, 'payroll/payroll_processing_result.html', {
#         'pay_period': pay_period,
#         'processed_count': processed_count,
#         'employees': employees
#     })

def calculate_payroll(request, pay_period_id):
    # ... (rest of your view code) ...

    payroll_results = []
    employees = Employee.objects.filter(is_active=True)
    pay_period = get_object_or_404(PayPeriod, pk=pay_period_id)
    processed_count = 0

    for employee in employees:
        payroll_exists = PayrollEntry.objects.filter(employee=employee, pay_period=pay_period).exists()
        payroll_entry = None
        if payroll_exists:
            payroll_entry = PayrollEntry.objects.get(employee=employee, pay_period=pay_period)

        payroll_results.append({
            'employee': employee,
            'payroll_exists': payroll_exists,
            'payroll_entry': payroll_entry,
        })

    return render(request, 'payroll/payroll_processing_result.html', {
        'pay_period': pay_period,
        'processed_count': processed_count,
        'payroll_results': payroll_results,
    })


class PayrollEntryListView(LoginRequiredMixin, ListView):
    model = PayrollEntry
    template_name = 'payroll/payrollentry_list.html'
    context_object_name = 'payroll_entries'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        pay_period_id = self.request.GET.get('pay_period')
        if pay_period_id:
            queryset = queryset.filter(pay_period__id=pay_period_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pay_periods'] = PayPeriod.objects.all().order_by('-end_date')
        return context

class PayrollEntryDetailView(LoginRequiredMixin, DetailView):
    model = PayrollEntry
    template_name = 'payroll/payrollentry_detail.html'
    context_object_name = 'payroll_entry'
