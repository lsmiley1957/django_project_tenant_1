# projects/admin.py

from django.contrib import admin
from .models import Project, Task, ProjectMember, TaskChecklistItem, TaskNote, TimeLog


# Register your models here to make them accessible in the Django admin interface.

@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'project')
    list_filter = ('role', 'project')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """
    Customizes the display of Project models in the Django admin.
    """
    list_display = ('name', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'start_date')
    search_fields = ('name', 'description')
    date_hierarchy = 'start_date' # Adds a date-based drilldown navigation

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    Customizes the display of Task models in the Django admin.
    """
    list_display = ('name', 'project', 'assigned_to', 'due_date', 'status')
    list_filter = ('status', 'project', 'assigned_to')
    search_fields = ('name', 'description', 'assigned_to')
    date_hierarchy = 'due_date'


@admin.register(TaskChecklistItem)
class TaskChecklistItemAdmin(admin.ModelAdmin):

    list_display = ('task', 'description', 'is_completed', 'position')
    list_filter = ('task', 'description')


@admin.register(TimeLog)
class TimeLogAdmin(admin.ModelAdmin):

    list_display = ('task', 'user', 'hours', 'date', 'description')


