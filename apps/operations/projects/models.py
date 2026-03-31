from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Sum

PROJECT_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
    ('on_hold', 'On Hold'),
    ('cancelled', 'Cancelled'),
]

TASK_STATUS_CHOICES = [
    ('todo', 'To Do'),
    ('pending', 'Pending'),
    ('in_progress', 'In Progress'),
    ('hold', 'On Hold'),
    ('blocked', 'Blocked'),
    ('done', 'Completed'),
]

ROLE_CHOICES = [
    ('sponsor', 'Project Sponsor'),
    ('member', 'Project Team Member'),
    ('stakeholder', 'Stakeholder'),
    ('resource_manager', 'Resource Manager'),
    ('vendor', 'Vendor/Contractor'),
]

class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=PROJECT_STATUS_CHOICES, default='pending')

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    @property
    def completion_percentage(self):
        total = self.tasks.count()
        if total == 0: return 0
        completed = self.tasks.filter(status='done').count()
        return int((completed / total) * 100)

    @property
    def total_logged_hours(self):
        total = TimeLog.objects.filter(task__project=self).aggregate(Sum('hours'))['hours__sum']
        return total or 0

    def total_effort(self):
        """Calculates total hours logged across all tasks in this project"""
        from django.db.models import Sum
        # Accessing all tasks, then all time_logs for those tasks
        return TimeLog.objects.filter(task__project=self).aggregate(total=Sum('hours'))['total'] or 0


class ProjectMember(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='member')

    def task_stats(self):
        tasks = self.assigned_tasks.all()
        total = tasks.count()
        open_tasks = tasks.exclude(status='done').count()
        completed = total - open_tasks

        # Calculate percentage safely
        percent = 0
        if total > 0:
            percent = (completed / total) * 100

        return {
            'total': total,
            'open': open_tasks,
            'completed': completed,
            'percent': round(percent)
        }
    def __str__(self):
        # This fixes "ProjectMember object(1)" showing in the dropdown
        return f"{self.name} ({self.get_role_display()})"

class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(ProjectMember, on_delete=models.SET_NULL, null=True, related_name='assigned_tasks')
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='todo')
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name

    def total_hours(self):
        return self.time_logs.aggregate(total=Sum('hours'))['total'] or 0


class TaskNote(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

class TimeLog(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='time_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)