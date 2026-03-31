You're asking for a significant amount of code and explanation to build a complete Django payroll application. This is a multi-faceted project involving database design, Django models, views, forms, URLs, and potentially user authentication, reporting, and more.

Instead of providing a single, monolithic code block, which would be overwhelming and difficult to understand, I'll break down the process into logical steps, providing key code snippets and explanations for each. This will give you a solid foundation and guide you through building the application yourself.

Core Components of a Django Payroll Application:

Project Setup: Initialize your Django project and app.
Database Design (Models): Define your data structures (employees, pay periods, timesheets, payroll entries, deductions, etc.).
Admin Interface: Make your models manageable through the Django admin.
Views & URLs: Define the logic for handling requests and mapping URLs to views.
Forms: Create forms for data input (e.g., adding employees, entering timesheets).
Templates: Design the user interface.
Basic Payroll Calculation Logic: A simplified example.
User Authentication (Optional but Recommended): For securing your application.
Step 1: Project Setup

First, make sure you have Python and pip installed.

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Django
pip install Django

# Create a new Django project
django-admin startproject payroll_project .

# Create a new Django app for payroll functionalities
python manage.py startapp payroll

# Add 'payroll' to INSTALLED_APPS in payroll_project/settings.py
In payroll_project/settings.py, find INSTALLED_APPS and add 'payroll', so it looks like:

# payroll_project/settings.py

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'payroll', # Add your app here
]
Step 2: Database Design (Models)

This is crucial. Think about the entities in a payroll system.

Open payroll/models.py and add the following:

# payroll/models.py
from django.db import models
from django.conf import settings # To link to Django's User model if needed

class Employee(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    date_of_hire = models.DateField()
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, help_text="Annual base salary")
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Hourly rate if applicable")
    is_active = models.BooleanField(default=True)
    bank_account_number = models.CharField(max_length=50, blank=True, null=True)
    tax_id_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"

class PayPeriod(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    name = models.CharField(max_length=100, blank=True, null=True) # e.g., "Bi-Weekly Pay Period 2025-01-01"

    class Meta:
        unique_together = ('start_date', 'end_date')
        ordering = ['-start_date']

    def __str__(self):
        if self.name:
            return self.name
        return f"Pay Period: {self.start_date} to {self.end_date}"

class TimeEntry(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    pay_period = models.ForeignKey(PayPeriod, on_delete=models.CASCADE)
    date = models.DateField()
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.employee.first_name} - {self.date}: {self.hours_worked} hrs"

class DeductionType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_tax_deduction = models.BooleanField(default=False) # e.g., 401k, health insurance, etc.

    def __str__(self):
        return self.name

class EmployeeDeduction(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    deduction_type = models.ForeignKey(DeductionType, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount per pay period")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.employee.first_name} - {self.deduction_type.name}: ${self.amount}"

class PayrollEntry(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    pay_period = models.ForeignKey(PayPeriod, on_delete=models.CASCADE)
    gross_pay = models.DecimalField(max_digits=10, decimal_places=2)
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    status = models.CharField(max_length=50, choices=[('pending', 'Pending'), ('processed', 'Processed'), ('paid', 'Paid')], default='pending')
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('employee', 'pay_period')
        ordering = ['-pay_period__end_date', 'employee__last_name']

    def __str__(self):
        return f"Payroll for {self.employee} ({self.pay_period.name}): ${self.net_pay}"
After defining models, run migrations:

python manage.py makemigrations payroll
python manage.py migrate
Step 3: Admin Interface

Register your models to manage them easily through Django's admin.

Open payroll/admin.py and add:

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
Now, create a superuser to access the admin:

python manage.py createsuperuser
Run the development server and visit http://127.0.0.1:8000/admin/:

python manage.py runserver
You should now be able to add employees, pay periods, etc., through the admin.

Step 4: Views & URLs

Let's create some basic views to display employee lists and detail, and a view to trigger payroll calculation for a pay period.

Open payroll/views.py:

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
def calculate_payroll(request, pay_period_id):
    if not request.user.is_authenticated:
        return redirect('login') # Assuming you have a login URL

    pay_period = get_object_or_404(PayPeriod, pk=pay_period_id)
    employees = Employee.objects.filter(is_active=True)
    processed_count = 0

    for employee in employees:
        # Check if payroll already exists for this employee and pay period
        if PayrollEntry.objects.filter(employee=employee, pay_period=pay_period).exists():
            continue # Skip if already processed

        total_hours = TimeEntry.objects.filter(
            employee=employee,
            pay_period=pay_period
        ).aggregate(Sum('hours_worked'))['hours_worked__sum'] or 0

        total_overtime_hours = TimeEntry.objects.filter(
            employee=employee,
            pay_period=pay_period
        ).aggregate(Sum('overtime_hours'))['overtime_hours__sum'] or 0

        gross_pay = 0.0

        if employee.hourly_rate:
            # Assuming standard hours are paid at hourly_rate, overtime at 1.5x
            gross_pay = (float(total_hours) * float(employee.hourly_rate)) + \
                        (float(total_overtime_hours) * float(employee.hourly_rate) * 1.5)
        elif employee.base_salary:
            # Simple division for salaried employees for a bi-weekly period (26 pay periods per year)
            # You'd need more sophisticated logic for monthly, semi-monthly, etc.
            gross_pay = float(employee.base_salary) / 26 # Example for bi-weekly

        # Calculate total deductions
        total_deductions = EmployeeDeduction.objects.filter(
            employee=employee,
            is_active=True
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        net_pay = gross_pay - float(total_deductions)

        PayrollEntry.objects.create(
            employee=employee,
            pay_period=pay_period,
            gross_pay=round(gross_pay, 2),
            total_deductions=round(float(total_deductions), 2),
            net_pay=round(net_pay, 2),
            payment_date=pay_period.end_date, # Or a separate payment date field
            status='processed'
        )
        processed_count += 1

    return render(request, 'payroll/payroll_processing_result.html', {
        'pay_period': pay_period,
        'processed_count': processed_count,
        'employees': employees
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

Now, define the URLs. Create payroll/urls.py:

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
Include these URLs in your main payroll_project/urls.py:

# payroll_project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('payroll.urls')), # Include your app's URLs
    # Add authentication URLs if you implement them (e.g., django.contrib.auth.urls)
    path('accounts/', include('django.contrib.auth.urls')), # Provides login, logout, etc.
]
Step 5: Forms

Create forms for your models.

Open payroll/forms.py:

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

Step 6: Templates

Create the HTML templates. Inside your payroll app, create a templates directory, and inside that, another payroll directory: payroll/templates/payroll/.

payroll/templates/payroll/base.html (Base template for consistent navigation)

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Django Payroll - {% block title %}{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { padding-top: 56px; } /* Adjust for fixed navbar */
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark fixed-top">
        <div class="container-fluid">
            <a class="navbar-brand" href="{% url 'home' %}">Payroll App</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                    <li class="nav-item">
                        <a class="nav-link" href="{% url 'employee_list' %}">Employees</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{% url 'payperiod_list' %}">Pay Periods</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{% url 'timeentry_add' %}">Add Time Entry</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{% url 'payrollentry_list' %}">Payroll Entries</a>
                    </li>
                </ul>
                <ul class="navbar-nav">
                    {% if user.is_authenticated %}
                        <li class="nav-item">
                            <span class="navbar-text me-3">
                                Welcome, {{ user.username }}
                            </span>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link btn btn-outline-light" href="{% url 'logout' %}">Logout</a>
                        </li>
                    {% else %}
                        <li class="nav-item">
                            <a class="nav-link btn btn-outline-light" href="{% url 'login' %}">Login</a>
                        </li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags }}">
                    {{ message }}
                </div>
            {% endfor %}
        {% endif %}

        {% block content %}
        {% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
payroll/templates/registration/login.html (For Django's built-in authentication)

{% extends "payroll/base.html" %}

{% block title %}Login{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h3>Login</h3>
            </div>
            <div class="card-body">
                <form method="post">
                    {% csrf_token %}
                    {{ form.as_p }}
                    <button type="submit" class="btn btn-primary">Login</button>
                    <input type="hidden" name="next" value="{{ next }}">
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
payroll/templates/payroll/employee_list.html

{% extends "payroll/base.html" %}

{% block title %}Employees{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
    <h2>Employees</h2>
    <a href="{% url 'employee_add' %}" class="btn btn-success">Add Employee</a>
</div>

<div class="table-responsive">
    <table class="table table-striped table-hover">
        <thead>
            <tr>
                <th>Name</th>
                <th>Employee ID</th>
                <th>Email</th>
                <th>Hire Date</th>
                <th>Salary/Rate</th>
                <th>Active</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for employee in employees %}
            <tr>
                <td><a href="{% url 'employee_detail' employee.pk %}">{{ employee.first_name }} {{ employee.last_name }}</a></td>
                <td>{{ employee.employee_id }}</td>
                <td>{{ employee.email }}</td>
                <td>{{ employee.date_of_hire|date:"M d, Y" }}</td>
                <td>
                    {% if employee.base_salary %}
                        ${{ employee.base_salary }} (Annual)
                    {% elif employee.hourly_rate %}
                        ${{ employee.hourly_rate }} (Hourly)
                    {% else %}
                        N/A
                    {% endif %}
                </td>
                <td>
                    {% if employee.is_active %}
                        <span class="badge bg-success">Active</span>
                    {% else %}
                        <span class="badge bg-danger">Inactive</span>
                    {% endif %}
                </td>
                <td>
                    <a href="{% url 'employee_edit' employee.pk %}" class="btn btn-sm btn-info">Edit</a>
                    <a href="{% url 'employee_delete' employee.pk %}" class="btn btn-sm btn-danger">Delete</a>
                </td>
            </tr>
            {% empty %}
            <tr>
                <td colspan="7">No employees found.</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
payroll/templates/payroll/employee_detail.html

{% extends "payroll/base.html" %}

{% block title %}{{ employee.first_name }} {{ employee.last_name }}{% endblock %}

{% block content %}
<div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h3>{{ employee.first_name }} {{ employee.last_name }} Details</h3>
        <div>
            <a href="{% url 'employee_edit' employee.pk %}" class="btn btn-warning btn-sm">Edit Employee</a>
            <a href="{% url 'employee_delete' employee.pk %}" class="btn btn-danger btn-sm">Delete Employee</a>
        </div>
    </div>
    <div class="card-body">
        <p><strong>Employee ID:</strong> {{ employee.employee_id }}</p>
        <p><strong>Email:</strong> {{ employee.email }}</p>
        <p><strong>Date of Hire:</strong> {{ employee.date_of_hire|date:"M d, Y" }}</p>
        <p><strong>Base Salary:</strong> {% if employee.base_salary %}${{ employee.base_salary }}{% else %}N/A{% endif %}</p>
        <p><strong>Hourly Rate:</strong> {% if employee.hourly_rate %}${{ employee.hourly_rate }}{% else %}N/A{% endif %}</p>
        <p><strong>Status:</strong> {% if employee.is_active %}<span class="badge bg-success">Active</span>{% else %}<span class="badge bg-danger">Inactive</span>{% endif %}</p>
        <p><strong>Bank Account:</strong> {{ employee.bank_account_number|default:"Not provided" }}</p>
        <p><strong>Tax ID:</strong> {{ employee.tax_id_number|default:"Not provided" }}</p>

        <h4 class="mt-4">Deductions</h4>
        {% if employee.employeededuction_set.all %}
        <ul class="list-group">
            {% for deduction in employee.employeededuction_set.all %}
                <li class="list-group-item">
                    {{ deduction.deduction_type.name }}: ${{ deduction.amount }} (Active: {{ deduction.is_active|yesno:"Yes,No" }})
                </li>
            {% endfor %}
        </ul>
        {% else %}
        <p>No deductions set for this employee.</p>
        {% endif %}

        <h4 class="mt-4">Recent Payroll Entries</h4>
        {% if employee.payrollentry_set.all %}
            <div class="table-responsive">
                <table class="table table-striped table-sm">
                    <thead>
                        <tr>
                            <th>Pay Period</th>
                            <th>Gross Pay</th>
                            <th>Deductions</th>
                            <th>Net Pay</th>
                            <th>Payment Date</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for payroll_entry in employee.payrollentry_set.all|slice:":5" %} {# Show last 5 #}
                        <tr>
                            <td><a href="{% url 'payrollentry_detail' payroll_entry.pk %}">{{ payroll_entry.pay_period.name|default:payroll_entry.pay_period }}</a></td>
                            <td>${{ payroll_entry.gross_pay }}</td>
                            <td>${{ payroll_entry.total_deductions }}</td>
                            <td>${{ payroll_entry.net_pay }}</td>
                            <td>{{ payroll_entry.payment_date|date:"M d, Y" }}</td>
                            <td><span class="badge bg-secondary">{{ payroll_entry.status|capfirst }}</span></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            <p><a href="{% url 'payrollentry_list' %}?employee={{ employee.pk }}">View all payroll entries for this employee</a></p>
        {% else %}
            <p>No payroll entries for this employee yet.</p>
        {% endif %}

    </div>
    <div class="card-footer">
        <a href="{% url 'employee_list' %}" class="btn btn-secondary">Back to Employees</a>
    </div>
</div>
{% endblock %}
payroll/templates/payroll/employee_form.html

{% extends "payroll/base.html" %}

{% block title %}
    {% if form.instance.pk %}Edit Employee{% else %}Add Employee{% endif %}
{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header">
                <h3>{% if form.instance.pk %}Edit Employee{% else %}Add New Employee{% endif %}</h3>
            </div>
            <div class="card-body">
                <form method="post">
                    {% csrf_token %}
                    {{ form.as_p }}
                    <button type="submit" class="btn btn-primary">Save</button>
                    <a href="{% url 'employee_list' %}" class="btn btn-secondary">Cancel</a>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
payroll/templates/payroll/employee_confirm_delete.html

{% extends "payroll/base.html" %}

{% block title %}Delete Employee{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card text-center border-danger">
            <div class="card-header bg-danger text-white">
                <h3>Confirm Deletion</h3>
            </div>
            <div class="card-body">
                <p>Are you sure you want to delete employee <strong>"{{ employee.first_name }} {{ employee.last_name }}"</strong>?</p>
                <p class="text-danger">This action cannot be undone.</p>
                <form method="post">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-danger me-2">Yes, Delete</button>
                    <a href="{% url 'employee_detail' employee.pk %}" class="btn btn-secondary">Cancel</a>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
payroll/templates/payroll/payperiod_list.html

{% extends "payroll/base.html" %}

{% block title %}Pay Periods{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
    <h2>Pay Periods</h2>
    <a href="{% url 'payperiod_add' %}" class="btn btn-success">Add Pay Period</a>
</div>

<div class="table-responsive">
    <table class="table table-striped table-hover">
        <thead>
            <tr>
                <th>Name</th>
                <th>Start Date</th>
                <th>End Date</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for pay_period in pay_periods %}
            <tr>
                <td>{{ pay_period.name|default:"N/A" }}</td>
                <td>{{ pay_period.start_date|date:"M d, Y" }}</td>
                <td>{{ pay_period.end_date|date:"M d, Y" }}</td>
                <td>
                    <a href="{% url 'calculate_payroll' pay_period.pk %}" class="btn btn-sm btn-primary">Process Payroll</a>
                    <a href="{% url 'payrollentry_list' %}?pay_period={{ pay_period.pk }}" class="btn btn-sm btn-info">View Payroll Entries</a>
                </td>
            </tr>
            {% empty %}
            <tr>
                <td colspan="4">No pay periods found.</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
payroll/templates/payroll/payperiod_form.html

{% extends "payroll/base.html" %}

{% block title %}Add Pay Period{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h3>Add New Pay Period</h3>
            </div>
            <div class="card-body">
                <form method="post">
                    {% csrf_token %}
                    {{ form.as_p }}
                    <button type="submit" class="btn btn-primary">Save</button>
                    <a href="{% url 'payperiod_list' %}" class="btn btn-secondary">Cancel</a>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
payroll/templates/payroll/timeentry_form.html

{% extends "payroll/base.html" %}

{% block title %}Add Time Entry{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h3>Add New Time Entry</h3>
            </div>
            <div class="card-body">
                <form method="post">
                    {% csrf_token %}
                    {{ form.as_p }}
                    <button type="submit" class="btn btn-primary">Save Time Entry</button>
                    <a href="{% url 'employee_list' %}" class="btn btn-secondary">Cancel</a>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
payroll/templates/payroll/payroll_processing_result.html

{% extends "payroll/base.html" %}

{% block title %}Payroll Processing Result{% endblock %}

{% block content %}
<div class="card">
    <div class="card-header">
        <h3>Payroll Processing Complete for {{ pay_period.name|default:pay_period }}</h3>
    </div>
    <div class="card-body">
        <p>Processed payroll for <strong>{{ processed_count }}</strong> employees.</p>
        <p class="mt-3"><strong>Details:</strong></p>
        <ul class="list-group">
            {% for employee in employees %}
                {% if employee.payrollentry_set.filter(pay_period=pay_period).exists %}
                    {% with payroll_entry=employee.payrollentry_set.get(pay_period=pay_period) %}
                        <li class="list-group-item list-group-item-success">
                            <strong>{{ employee.first_name }} {{ employee.last_name }}:</strong> Gross Pay: ${{ payroll_entry.gross_pay }}, Net Pay: ${{ payroll_entry.net_pay }}
                        </li>
                    {% endwith %}
                {% else %}
                    <li class="list-group-item list-group-item-warning">
                        <strong>{{ employee.first_name }} {{ employee.last_name }}:</strong> Not processed (either skipped or no time entries).
                    </li>
                {% endif %}
            {% endfor %}
        </ul>
    </div>
    <div class="card-footer">
        <a href="{% url 'payrollentry_list' %}" class="btn btn-primary">View All Payroll Entries</a>
        <a href="{% url 'payperiod_list' %}" class="btn btn-secondary">Back to Pay Periods</a>
    </div>
</div>
{% endblock %}
payroll/templates/payroll/payrollentry_list.html

{% extends "payroll/base.html" %}

{% block title %}Payroll Entries{% endblock %}

{% block content %}
<h2>Payroll Entries</h2>

<div class="mb-3">
    <form method="get" action="{% url 'payrollentry_list' %}" class="row g-3 align-items-center">
        <div class="col-auto">
            <label for="pay_period_filter" class="col-form-label">Filter by Pay Period:</label>
        </div>
        <div class="col-auto">
            <select name="pay_period" id="pay_period_filter" class="form-select">
                <option value="">All Pay Periods</option>
                {% for pp in pay_periods %}
                    <option value="{{ pp.id }}" {% if request.GET.pay_period|stringformat:"s" == pp.id|stringformat:"s" %}selected{% endif %}>
                        {{ pp.name|default:pp }}
                    </option>
                {% endfor %}
            </select>
        </div>
        <div class="col-auto">
            <button type="submit" class="btn btn-primary">Filter</button>
        </div>
        <div class="col-auto">
            {% if request.GET.pay_period %}
                <a href="{% url 'payrollentry_list' %}" class="btn btn-secondary">Clear Filter</a>
            {% endif %}
        </div>
    </form>
</div>


<div class="table-responsive">
    <table class="table table-striped table-hover">
        <thead>
            <tr>
                <th>Employee</th>
                <th>Pay Period</th>
                <th>Gross Pay</th>
                <th>Deductions</th>
                <th>Net Pay</th>
                <th>Payment Date</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for entry in payroll_entries %}
            <tr>
                <td><a href="{% url 'employee_detail' entry.employee.pk %}">{{ entry.employee.first_name }} {{ entry.employee.last_name }}</a></td>
                <td>{{ entry.pay_period.name|default:entry.pay_period }}</td>
                <td>${{ entry.gross_pay }}</td>
                <td>${{ entry.total_deductions }}</td>
                <td>${{ entry.net_pay }}</td>
                <td>{{ entry.payment_date|date:"M d, Y" }}</td>
                <td><span class="badge bg-{% if entry.status == 'paid' %}success{% elif entry.status == 'processed' %}info{% else %}secondary{% endif %}">{{ entry.status|capfirst }}</span></td>
                <td>
                    <a href="{% url 'payrollentry_detail' entry.pk %}" class="btn btn-sm btn-info">View</a>
                </td>
            </tr>
            {% empty %}
            <tr>
                <td colspan="8">No payroll entries found.</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

{% if is_paginated %}
    <nav aria-label="Page navigation">
        <ul class="pagination justify-content-center">
            {% if page_obj.has_previous %}
                <li class="page-item"><a class="page-link" href="?page={{ page_obj.previous_page_number }}{% if request.GET.pay_period %}&pay_period={{ request.GET.pay_period }}{% endif %}">Previous</a></li>
            {% endif %}

            {% for i in page_obj.paginator.page_range %}
                <li class="page-item {% if page_obj.number == i %}active{% endif %}"><a class="page-link" href="?page={{ i }}{% if request.GET.pay_period %}&pay_period={{ request.GET.pay_period }}{% endif %}">{{ i }}</a></li>
            {% endfor %}

            {% if page_obj.has_next %}
                <li class="page-item"><a class="page-link" href="?page={{ page_obj.next_page_number }}{% if request.GET.pay_period %}&pay_period={{ request.GET.pay_period }}{% endif %}">Next</a></li>
            {% endif %}
        </ul>
    </nav>
{% endif %}

{% endblock %}
payroll/templates/payroll/payrollentry_detail.html

{% extends "payroll/base.html" %}

{% block title %}Payroll Entry Details{% endblock %}

{% block content %}
<div class="card">
    <div class="card-header">
        <h3>Payroll Details for {{ payroll_entry.employee.first_name }} {{ payroll_entry.employee.last_name }} ({{ payroll_entry.pay_period.name|default:payroll_entry.pay_period }})</h3>
    </div>
    <div class="card-body">
        <p><strong>Employee:</strong> <a href="{% url 'employee_detail' payroll_entry.employee.pk %}">{{ payroll_entry.employee }}</a></p>
        <p><strong>Pay Period:</strong> {{ payroll_entry.pay_period.name|default:payroll_entry.pay_period }}</p>
        <p><strong>Gross Pay:</strong> ${{ payroll_entry.gross_pay }}</p>
        <p><strong>Total Deductions:</strong> ${{ payroll_entry.total_deductions }}</p>
        <p><strong>Net Pay:</strong> ${{ payroll_entry.net_pay }}</p>
        <p><strong>Payment Date:</strong> {{ payroll_entry.payment_date|date:"M d, Y" }}</p>
        <p><strong>Status:</strong> <span class="badge bg-secondary">{{ payroll_entry.status|capfirst }}</span></p>
        {% if payroll_entry.notes %}
            <p><strong>Notes:</strong> {{ payroll_entry.notes|linebreaksbr }}</p>
        {% endif %}
    </div>
    <div class="card-footer">
        <a href="{% url 'payrollentry_list' %}" class="btn btn-secondary">Back to Payroll Entries</a>
    </div>
</div>
{% endblock %}
Running the Application:

Make sure your virtual environment is active.
Run migrations: python manage.py makemigrations payroll and python manage.py migrate
Create a superuser: python manage.py createsuperuser (if you haven't already)
Start the development server: python manage.py runserver
Now, navigate to http://127.0.0.1:8000/. You should be redirected to the login page (if you included path('accounts/', include('django.contrib.auth.urls')) and LoginRequiredMixin). Log in with your superuser credentials.

To Test the Payroll Calculation:

Go to http://127.0.0.1:8000/admin/ and add some Employee objects. Make sure to set base_salary or hourly_rate.
Add some PayPeriod objects.
Add TimeEntry objects for employees and the pay periods you created.
Go to the Pay Periods list (/payperiods/) and click "Process Payroll" next to a pay period.
Then go to Payroll Entries (/payroll/) to see the results.
Further Enhancements (Beyond this Basic Example):

Robust Payroll Logic: The calculation is very basic. A real payroll system needs to handle:
Federal, state, and local taxes (income tax, FICA, etc.)
Different pay frequencies (weekly, bi-weekly, semi-monthly, monthly)
Pre-tax and post-tax deductions
Benefits (health, dental, 401k matching)
Bonuses, commissions, reimbursements
Integration with tax services or accounting software
Overtime rules (e.g., California rules vs. federal)
Reporting: Generate pay stubs, payroll summaries, tax reports (W-2, 1099).
User Roles & Permissions: Different users (e.g., HR, managers, employees) should have different access levels.
Employee Self-Service Portal: Employees can view their pay stubs, update personal info, submit time-off requests.
Time Tracking Integration: More advanced time tracking, possibly with punch-in/punch-out.
Error Handling and Validation: More robust validation in forms and views.
Notifications: Email notifications for processed payroll.
Scheduled Tasks: Use Django-Q or Celery to schedule payroll processing automatically.
Frontend Framework: For a richer user experience, consider integrating with React, Vue, or Angular.
This provides a strong starting point for your Django Payroll Application. Remember that building a full-featured payroll system is complex due to the legal and financial implications, so start simple and build incrementally.