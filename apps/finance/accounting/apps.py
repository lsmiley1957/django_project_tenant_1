from django.apps import AppConfig


class AccountingConfig(AppConfig):
    # Using the full path ensures Django's app registry can map it correctly
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.finance.accounting'
    label = 'accounting'
    verbose_name = 'Accounting'