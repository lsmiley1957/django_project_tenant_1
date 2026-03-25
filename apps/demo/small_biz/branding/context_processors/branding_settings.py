from apps.demo.small_biz.branding.models import Branding


def branding_settings(request):
    """
    Makes company branding and financial constants available
    globally in all Django templates.
    """
    try:
        config = Branding.objects.first()
    except:
        config = None

    return {
        'site_branding': config
    }