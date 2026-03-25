from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum

class SalesProfile(models.Model):
    """Tracks availability and last assignment for sales team members"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_active_for_leads = models.BooleanField(default=True)
    last_assigned_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Sales Profile: {self.user.username}"

class Stage(models.Model):
    """The dynamic columns for your Kanban board"""
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Acct_customer(models.Model):
    """Upgraded CRM Customer Model with Pipeline & Analytics"""
    STATUS_CHOICES = [
        ('LEAD', 'New Lead'),
        ('DISCOVERY', 'Discovery'),  # New Column
        ('QUALIFIED', 'Qualified'),
        ('PROPOSAL', 'Proposal Sent'),  # New Column
        ('NEGOTIATION', 'Negotiation'),
        ('WON', 'Won / Onboarding'),  # New Column
        ('ACTIVE', 'Active Client'),
        ('LOST', 'Lost / Archive'),
    ]

    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True)

    # CRM & Pipeline
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='LEAD')
    source = models.CharField(max_length=100, blank=True, default='Manual Entry')
    stage = models.ForeignKey(Stage, on_delete=models.SET_NULL, null=True, related_name='customers')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # Analytics: Customer Lifetime Value (Step #4)
    # Inside your Acct_customer model
    def get_lifetime_value(self):
        """Calculates LTV with a safety check for the relationship"""
        if not hasattr(self, 'postransaction_set'):
            return 0.00

        total = self.postransaction_set.aggregate(total=Sum('total_price'))['total']
        return total or 0.00

    def __str__(self):
        return self.name


class CustomerActivity(models.Model):
    """Step #2: Interaction Timeline"""
    TYPE_CHOICES = [
        ('CALL', 'Phone Call'), ('EMAIL', 'Email'),
        ('MEETING', 'Meeting'), ('SALE', 'Purchase Made'), ('NOTE', 'Note')
    ]
    customer = models.ForeignKey(Acct_customer, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    activity_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='NOTE')
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


class CustomerTask(models.Model):
    """Step #5: Task & Reminder System"""
    customer = models.ForeignKey(Acct_customer, on_delete=models.CASCADE, related_name='tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    due_date = models.DateTimeField()
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)




