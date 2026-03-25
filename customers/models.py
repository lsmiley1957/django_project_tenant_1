# customers/models.py
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

from registry.models import GlobalApp


class Client(TenantMixin):
    name = models.CharField(max_length=100)
    paid_until = models.DateField()
    on_trial = models.BooleanField()
    created_on = models.DateField(auto_now_add=True)

    PLAN_CHOICES = [
        ('basic', 'Basic Plan'),
        ('premium', 'Premium Plan'),
    ]
    plan = models.CharField(max_length=10, choices=PLAN_CHOICES, default='basic')
    # A tenant 'subscribes' to global apps from the registry
    active_subscriptions = models.ManyToManyField(GlobalApp, blank=True)

    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = True

class Domain(DomainMixin):
    pass