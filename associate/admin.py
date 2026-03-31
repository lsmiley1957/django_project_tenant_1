from django.contrib import admin
from django.utils.html import format_html
from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from django.db import ProgrammingError, connection

from .models import (
    EmploymentStatus, Department, Position,
    PayBand, WorkLocation, Associate,
    AppSettings, CompanyPolicy, PerformanceReview, SalaryHistory, UserSubmission, CKTemplate, TemplateCategory
)


@admin.register(EmploymentStatus)
class EmploymentStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_preview')

    def color_preview(self, obj):
        if obj.color_code:
            # FIX: Providing the color_code as an argument to format_html
            return format_html(
                '<div style="width: 20px; height: 20px; background: {}; border-radius: 50%;"></div>',
                obj.color_code
            )
        return "No Color"


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'manager_link')
    search_fields = ('name', 'code')

    def manager_link(self, obj):
        if obj.manager:
            return obj.manager.user.get_full_name()
        return "No Manager Assigned"

    manager_link.short_description = "Manager"


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # 1. Check if we are in the public schema
        # Tenant apps should not be 'added' to the public schema
        if connection.schema_name == 'public':
            return False

        # 2. Check if the table exists before querying to prevent the 500 error
        try:
            if AppSettings.objects.exists():
                return False # Only allow one settings object
            return True
        except ProgrammingError:
            # Table doesn't exist in this schema yet
            return False

    def has_module_permission(self, request):
        # Hide the entire module from the sidebar if on the public schema
        if connection.schema_name == 'public':
            return False
        return super().has_module_permission(request)

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'is_management')
    list_filter = ('is_management',)
    search_fields = ('title', 'code')


@admin.register(PayBand)
class PayBandAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_salary', 'max_salary', 'currency')


@admin.register(WorkLocation)
class WorkLocationAdmin(admin.ModelAdmin):
    # Removed 'timezone' and 'is_virtual' as they aren't in your model
    list_display = ('name', 'city', 'country')
    search_fields = ('name', 'city', 'country')



@admin.register(Associate)
class AssociateAdmin(admin.ModelAdmin):
    # Ensure any method using format_html provides args/kwargs
    list_display = ('get_name', 'associate_id', 'phone', 'department', 'position', 'status_badge')
    list_filter = ('department', 'status', 'work_location')
    search_fields = ('user__first_name', 'user__last_name', 'associate_id', 'user__email')
    readonly_fields = ('associate_id',)

    def get_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_name.short_description = 'Name'

    def status_badge(self, obj):
        if obj.status:
            # FIX: Ensure format_html has the variables passed as separate arguments
            # Incorrect: format_html(f'<span style="color: {obj.status.color_code}">{obj.status.name}</span>')
            # Correct:
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                obj.status.color_code,
                obj.status.name
            )
        return "-"
    status_badge.short_description = 'Status'


@admin.register(CompanyPolicy)
class CompanyPolicyAdmin(admin.ModelAdmin):
    # Removed 'timezone' and 'is_virtual' as they aren't in your model
    list_display = ('title', 'category', 'created_at', 'is_active')
    search_fields = ('title', 'category')


@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    # Removed 'timezone' and 'is_virtual' as they aren't in your model
    list_display = ('associate', 'reviewer', 'review_date', 'performance_rating', 'feedback', 'goals_for_next_period')
    search_fields = ('associate', 'reviewer', 'performance_rating')


@admin.register(SalaryHistory)
class SalaryHistoryAdmin(admin.ModelAdmin):

    list_display = ('associate', 'amount', 'change_reason', 'effective_date', 'created_at')
    search_fields = ('associate', 'amount')


@admin.register(UserSubmission)
class UserSubmissionAdmin(admin.ModelAdmin):

    list_display = ('user', 'base_template', 'filled_content', 'is_draft', 'created_at',)
    list_filter = ('base_template','is_draft',)


# CKTemplate

class CKTemplateAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure the 'content' field uses the 'extends' config defined in settings.py
        self.fields["content"].widget = CKEditor5Widget(
            attrs={"class": "django_ckeditor_5"},
            config_name="extends"
        )

    class Meta:
        model = CKTemplate
        fields = "__all__"

@admin.register(CKTemplate)
class CKTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'category', 'created_at', 'updated_at')
    list_filter = ('category', 'title')


@admin.register(TemplateCategory)
class TemplateCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon',)
    search_fields = ('name',)

