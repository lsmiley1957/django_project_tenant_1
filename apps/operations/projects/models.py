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


class ProjectMember(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')

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

    # Task-to-Task linking (Predecessors)
    dependencies = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='dependent_tasks',
        blank=True
    )

    def __str__(self):
        return self.name

    def total_hours(self):
        return self.time_logs.aggregate(total=Sum('hours'))['total'] or 0

    @property
    def completion_percentage(self):
        """Calculates progress based on checklist items, or status if no checklist exists."""
        steps = self.checklist_items.all()
        if not steps.exists():
            return 100 if self.status == 'done' else 0

        completed_count = steps.filter(is_completed=True).count()
        return int((completed_count / steps.count()) * 100)


class TaskChecklistItem(models.Model):
    """Handles step-by-step requirements within a single task."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='checklist_items')
    description = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.task.name} - {self.description}"


class TaskNote(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)


class TimeLog(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='time_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.hours}h on {self.task.name}"