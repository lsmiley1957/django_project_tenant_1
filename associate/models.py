from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field
from django.utils.text import slugify
from decimal import Decimal
from django.conf import settings
# Import your Global Registry model (adjust path if your app name is different)
from registry.models import GlobalApp




class Position(models.Model):
    """Dynamic table for Job Titles/Roles."""
    title = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True, blank=True)
    is_management = models.BooleanField(default=False, help_text="Grants administrative dashboard access")
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']


class PayBand(models.Model):
    """Defines salary grades and compensation ranges."""
    name = models.CharField(max_length=50, unique=True, null=True, blank=True, )
    min_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, )
    max_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, )
    currency = models.CharField(max_length=3, default='USD')

    def __str__(self):
        return f"{self.name} ({self.min_salary} - {self.max_salary})"


class EmploymentStatus(models.Model):
    """Dynamic status types (e.g., Full-Time, Contractor, Intern, On Leave)."""
    name = models.CharField(max_length=50, unique=True)
    is_active_status = models.BooleanField(default=True)
    color_code = models.CharField(max_length=20, default="#2dce89", null=True, blank=True)

    def __str__(self):
        return self.name


class WorkLocation(models.Model):
    """Physical or Virtual office locations."""
    name = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.city})" if self.city else self.name


class Department(models.Model):
    """
    Department definition.
        Manager is a string reference to avoid the 'Chicken and Egg' circular import.
    """
    name = models.CharField(max_length=100, null=True, blank=True)
    code = models.CharField(max_length=10, unique=True, null=True, blank=True)
    manager = models.ForeignKey(
        'Associate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments'
    )

    def __str__(self):
        return self.name

class TenantAppInstallation(models.Model):
    """
    Tracks which Global Apps are 'installed' or 'activated' for this specific tenant.
    """
    # Use string reference to avoid 'Already Registered' warnings
    app = models.ForeignKey(
        'registry.GlobalApp',
        on_delete=models.PROTECT,
        related_name='installations'
    )
    installed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(
        default=True,
        help_text="If false, this app is hidden from the tenant's dashboard."
    )
    installed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        # A tenant schema technically only has one 'set' of installs,
        # so we ensure an app isn't installed twice in this schema.
        unique_together = ('app',)
        verbose_name = "Tenant App Installation"
        verbose_name_plural = "Tenant App Installations"

    def __str__(self):
        # We try to access the name, but carefully in case of related object issues
        return f"Installation: {self.app_id}"


class UserAppAssignment(models.Model):
    """
    The final link: Connects a specific User to a specific Global Role
    within an installed App.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='associate_app_assignments')
    # FIXED: Changed 'on_object' to 'on_delete'
    installation = models.ForeignKey(TenantAppInstallation, on_delete=models.CASCADE)
    # Reference to the blueprint role
    role = models.ForeignKey('registry.GlobalRole', on_delete=models.CASCADE)

    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevents assigning the same user multiple roles in one app instance
        unique_together = ('user', 'installation')
        verbose_name = "User App Assignment"
        verbose_name_plural = "User App Assignments"

    def __str__(self):
        return f"{self.user.username} - {self.installation.app.name} ({self.role.name})"


class AppSettings(models.Model):
    """
    Central configuration for SaaS customers to define their
    organization's formatting and sequences.
    """
    starting_associate_number = models.PositiveIntegerField(default=1000)
    current_sequence_value = models.PositiveIntegerField(default=0)
    associate_id_prefix = models.CharField(max_length=10, default="EMP", help_text="e.g. EMP")
    associate_id_suffix = models.CharField(max_length=10, blank=True, help_text="e.g. HQ")
    use_year_in_id = models.BooleanField(default=True)
    admin_users = models.ManyToManyField(User, related_name='admin_of_apps', blank=True)

    class Meta:
        verbose_name = "App Setting"
        verbose_name_plural = "App Settings"

    def __str__(self):
        return "Global Configuration"

    @classmethod
    def get_settings(cls):
        """Helper to get settings or return a default instance to avoid crashes."""
        settings = cls.objects.first()
        if not settings:
            # Returns an unsaved instance with defaults if none exists in DB
            return cls()
        return settings


class Associate(models.Model):
    """Main profile for an employee/contractor with dynamic ID generation and leave tracking."""

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('P', 'Prefer not to say'),
    ]

    ETHNIC_CHOICES = [
        ('W', 'White'),
        ('H', 'Hispanic'),
        ('B', 'Black'),
        ('A', 'Asian'),
        ('O', 'Other'),
        ('P', 'Prefer not to say'),
    ]

    # Identity
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='associate_profile')
    associate_id = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        help_text="Leave blank to auto-generate based on App Settings"
    )

    # Organization
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, related_name='members')
    position = models.ForeignKey('Position', on_delete=models.SET_NULL, null=True)
    reports_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='direct_reports')
    work_location = models.ForeignKey('WorkLocation', on_delete=models.SET_NULL, null=True)

    # Pay & Status
    pay_band = models.ForeignKey('PayBand', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.ForeignKey('EmploymentStatus', on_delete=models.PROTECT, related_name='associates')

    # Vital Stats
    hire_date = models.DateField(default=timezone.now)
    termination_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)

    # Financials & Contact
    current_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    gender = models.CharField(max_length=30, choices=GENDER_CHOICES, default='P')
    ethnicity = models.CharField(max_length=30, choices=ETHNIC_CHOICES, default='P', blank=True)

    phone = models.CharField(max_length=20, blank=True)
    personal_email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    address2 = models.TextField(blank=True)
    city = models.TextField(blank=True)
    state = models.TextField(blank=True)
    zip = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    # Leave & PTO Tracking
    sick_leave_used = models.DecimalField(max_digits=5, decimal_places=2, default=0.00,
                                          help_text="Total sick leave used")
    annual_leave_used = models.DecimalField(max_digits=5, decimal_places=2, default=0.00,
                                            help_text="Total annual leave used")
    other_leave_used = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Other leave used")

    pto_accrued = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, help_text="Total PTO accrued")
    pto_used = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, help_text="Total PTO used")
    pto_balance = models.DecimalField(max_digits=6, decimal_places=2, default=0.00,
                                      help_text="Calculated remaining balance")

    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)

    @property
    def get_avatar_url(self):
        # Check for uploaded profile picture first
        if self.profile_picture:
            return self.profile_picture.url

        # Determine the name to use for the placeholder avatar
        name = "User"
        if self.user and self.user.first_name:
            name = self.user.first_name

        return f"https://ui-avatars.com/api/?background=0d9488&color=fff&name={name}"

    @property
    def display_name(self):
        if self.user:
            return f"{self.user.first_name} {self.user.last_name}"
        return str(self)

    @property
    def get_dropdown_label(self):
        """Returns label for select dropdowns: Name (Position)"""
        name = self.user.get_full_name() or self.user.username
        pos = self.position.title if self.position else "No Position"
        return f"{name} ({pos})"

    def save(self, *args, **kwargs):
        # --- NEW: Robust PTO Calculation to fix 'str - str' error ---
        try:
            # Ensure values are treated as Decimals/Numbers before calculation
            # We use float/decimal casting here as a safety net for AJAX inputs
            accrued = Decimal(str(self.pto_accrued or 0))
            used = Decimal(str(self.pto_used or 0))
            self.pto_balance = accrued - used
        except (TypeError, ValueError, Decimal.InvalidOperation):
            self.pto_balance = 0.00

        # --- Existing Associate ID Generation Logic ---
        if not self.associate_id:
            with transaction.atomic():
                # Import AppSettings inside to avoid circular imports if necessary
                from .models import AppSettings
                settings, created = AppSettings.objects.get_or_create(id=1)
                settings = AppSettings.objects.select_for_update().get(id=settings.id)

                if settings.current_sequence_value == 0:
                    next_val = settings.starting_associate_number
                else:
                    next_val = settings.current_sequence_value + 1

                parts = []
                if settings.associate_id_prefix: parts.append(settings.associate_id_prefix)
                if settings.use_year_in_id: parts.append(str(timezone.now().year))
                parts.append(f"{next_val:04d}")
                if settings.associate_id_suffix: parts.append(settings.associate_id_suffix)

                self.associate_id = "-".join(parts)
                settings.current_sequence_value = next_val
                settings.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_dropdown_label


class SalaryHistory(models.Model):
    associate = models.ForeignKey(Associate, on_delete=models.CASCADE, related_name='salary_history')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    change_reason = models.CharField(max_length=255, help_text="e.g., Annual Raise, Promotion")
    effective_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        ordering = ['-effective_date']


class PerformanceReview(models.Model):
    """
    Comprehensive Performance Review Model.
    Includes Quantitative OKRs/KPIs, Qualitative Competency Ratings,
    Development Planning, and Administrative Tracking.
    """
    STATUS_CHOICES = [('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved')]
    RATING_SCALE = [(1, 'Unsatisfactory'), (2, 'Needs Improvement'), (3, 'Meets Expectations'),
                    (4, 'Exceeds Expectations'), (5, 'Exceptional')]

    associate = models.ForeignKey(Associate, on_delete=models.CASCADE, related_name='reviews',
                                  help_text="The employee being reviewed")
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reviews_conducted',
                                 help_text="Direct supervisor")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    review_date = models.DateField(default=timezone.now)
    review_period_start = models.DateField(null=True, blank=True)
    review_period_end = models.DateField(null=True, blank=True)
    next_review_date = models.DateField(null=True, blank=True)

    performance_rating = models.IntegerField(choices=RATING_SCALE, null=True, blank=True)
    okr_summary = models.TextField(blank=True, null=True, help_text="Objectives and Key Results Progress")
    kpi_metrics = models.JSONField(default=dict, blank=True, help_text="Role-specific metrics")
    project_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00,
                                                  help_text="Percentage finished on time")

    leadership_rating = models.IntegerField(choices=RATING_SCALE, default=3)
    communication_rating = models.IntegerField(choices=RATING_SCALE, default=3)
    technical_ability_rating = models.IntegerField(choices=RATING_SCALE, default=3)

    feedback = CKEditor5Field('Executive Feedback', config_name='extends')
    self_assessment_score = models.IntegerField(choices=RATING_SCALE, null=True, blank=True)
    self_assessment_comments = models.TextField(blank=True, null=True)
    peer_feedback_summary = models.TextField(blank=True, null=True, help_text="Feedback from colleagues")

    skills_gap_analysis = models.TextField(blank=True, null=True, help_text="Areas needing improvement")
    training_progress = models.TextField(blank=True, null=True, help_text="Courses taken")
    goals_for_next_period = models.TextField(blank=True, null=True)
    goals_met = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['-review_date']
        verbose_name = "Performance Review"
        verbose_name_plural = "Performance Reviews"

    def __str__(self):
        name = self.associate.user.get_full_name() if self.associate and self.associate.user else "Unknown"
        return f"Review: {name} ({self.review_period_start})"

    @property
    def is_complete(self):
        return self.status == 'approved'


class CompanyPolicy(models.Model):
    CATEGORY_CHOICES = [('General', 'General'), ('Benefits', 'Benefits'), ('Conduct', 'Conduct'), ('Safety', 'Safety')]
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    content = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='General')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class AssociateDocument(models.Model):
    associate = models.ForeignKey(Associate, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=50)
    file = models.FileField(upload_to='associate_docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


class TemplateCategory(models.Model):
    """Categories for the form library."""
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, help_text="Lucide icon name or Emoji")

    class Meta:
        verbose_name_plural = "Template Categories"

    def __str__(self):
        return self.name


class CKTemplate(models.Model):
    """Library of available forms/documents."""
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    # UPDATED: Changed from TextField to CKEditor5Field for better Admin UX
    content = CKEditor5Field(config_name='extends', help_text="The raw HTML/CKEditor content for the template")
    category = models.ForeignKey('TemplateCategory', on_delete=models.SET_NULL, null=True, related_name="templates")
    thumbnail_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class UserSubmission(models.Model):
    """The actual filled-out form saved by the user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    base_template = models.ForeignKey(CKTemplate, on_delete=models.SET_NULL, null=True)
    filled_content = models.TextField()
    is_draft = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s version of {self.base_template.title if self.base_template else 'Doc'}"