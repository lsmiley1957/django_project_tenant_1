# crm_project/crm/models.py

from django.db import models
from django.contrib.auth.models import User  # Import Django's built-in User model


# Model for Sales Territories
class Territory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Territories"  # Correct pluralization for admin

    def __str__(self):
        return self.name


# Model for Leads
class Lead(models.Model):
    # Choices for Lead Source
    LEAD_SOURCE_CHOICES = [
        ('Website', 'Website'),
        ('Referral', 'Referral'),
        ('Cold Call', 'Cold Call'),
        ('Event', 'Event'),
        ('Other', 'Other'),
    ]

    # Choices for Lead Status
    LEAD_STATUS_CHOICES = [
        ('New', 'New'),
        ('Contacted', 'Contacted'),
        ('Qualified', 'Qualified'),
        ('Disqualified', 'Disqualified'),
        ('Converted', 'Converted'),  # Lead converted to Opportunity
    ]

    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    source = models.CharField(max_length=50, choices=LEAD_SOURCE_CHOICES, default='Website')
    status = models.CharField(max_length=50, choices=LEAD_STATUS_CHOICES, default='New')
    description = models.TextField(blank=True, null=True)

    # Assign lead to a specific user (sales representative)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')

    # Assign lead to a specific territory
    territory = models.ForeignKey(Territory, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # Order leads by creation date, newest first

    def __str__(self):
        return self.name


# Model for Opportunities
class Opportunity(models.Model):
    # Choices for Opportunity Stage
    OPPORTUNITY_STAGE_CHOICES = [
        ('Prospecting', 'Prospecting'),
        ('Qualification', 'Qualification'),
        ('Needs Analysis', 'Needs Analysis'),
        ('Value Proposition', 'Value Proposition'),
        ('Perception Analysis', 'Perception Analysis'),
        ('Proposal/Quote', 'Proposal/Quote'),
        ('Negotiation/Review', 'Negotiation/Review'),
        ('Closed Won', 'Closed Won'),
        ('Closed Lost', 'Closed Lost'),
    ]

    # An opportunity can originate from a lead
    lead = models.OneToOneField(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunity')

    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stage = models.CharField(max_length=50, choices=OPPORTUNITY_STAGE_CHOICES, default='Prospecting')
    close_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # Assign opportunity to a specific user (sales representative)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='opportunities')

    # Assign opportunity to a specific territory
    territory = models.ForeignKey(Territory, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='opportunities')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # Order opportunities by creation date, newest first
        verbose_name_plural = "Opportunities"  # Correct pluralization for admin

    def __str__(self):
        return f"{self.name} - {self.stage}"