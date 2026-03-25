from django.db import models
from django.contrib.auth.models import User

class Parent(models.Model):
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Child(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='children')
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='child_profile', null=True, blank=True)

    def __str__(self):
        return self.name

class Chore(models.Model):
    CHORE_CATEGORIES = [
        ('kitchen', 'Kitchen'),
        ('bedroom', 'Bedroom'),
        ('bathroom', 'Bathroom'),
        ('outside', 'Outside'),
        ('other', 'Other'),
    ]
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50, choices=CHORE_CATEGORIES, default='other')
    base_points = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class ChoreAssignment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
        ('failed', 'Failed'),
    ]
    chore = models.ForeignKey(Chore, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.chore.name} assigned to {self.assigned_to.username}"

class ComputerTime(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='computer_times')
    date = models.DateField(auto_now_add=True)
    minutes_allowed = models.IntegerField(default=60)
    minutes_used = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.child.name} - {self.date}"

class Reward(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    point_cost = models.IntegerField()
    stock = models.IntegerField(default=-1, help_text="-1 for infinite")
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class PointTransaction(models.Model):
    TYPE_CHOICES = [('earn', 'Earned'), ('spend', 'Spent')]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    related_assignment = models.ForeignKey(ChoreAssignment, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}: {self.amount}"