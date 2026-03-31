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
