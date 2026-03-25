from django.apps import AppConfig

class BrandingConfig(AppConfig):
    # Using the full path ensures Django's app registry can map it correctly
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.demo.small_biz.branding'
    label = 'branding'
    verbose_name = 'Company Branding & Registry'