# customers signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Client, Domain


# @receiver(post_save, sender=Client)
# def create_tenant_domain(sender, instance, created, **kwargs):
#     if created:
#         # Check if it's the public schema; we usually handle that manually
#         # or give it a specific root domain.
#         if instance.schema_name == 'public':
#             domain_name = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost'
#         else:
#             # Logic: slugify the name or use the schema_name as the subdomain
#             domain_name = f"{instance.schema_name}.localhost"
#
#         Domain.objects.create(
#             domain=domain_name,
#             tenant=instance,
#             is_primary=True
#         )


@receiver(post_save, sender=Client)
def create_tenant_domain(sender, instance, created, **kwargs):
    """
    Automatic domain creation for internal/automated processes.
    NOTE: In the manual signup view, we often handle this manually
    to control the exact domain string and error handling.
    """
    if created:
        # Check if a domain already exists to avoid IntegrityErrors
        if not Domain.objects.filter(tenant=instance).exists():
            if instance.schema_name == 'public':
                domain_name = 'localhost'
            else:
                domain_name = f"{instance.schema_name}.localhost"

            Domain.objects.create(
                domain=domain_name,
                tenant=instance,
                is_primary=True
            )