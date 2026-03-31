from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from core import settings


# from marketplace.models import App


class LandingPageView(TemplateView):
    """
    Class-Based View for the public landing page.
    """
    template_name = 'landing.html'

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['services'] = [
    #         {'title': 'Cloud Hosting', 'description': 'Secure and scalable hosting for your data_seeds.'},
    #         {'title': 'API Access', 'description': 'Connect your workflow with our robust REST API.'},
    #         {'title': 'Custom Domains', 'description': 'Branding made easy with dedicated subdomains.'},
    #     ]
    #     context['apps'] = [
    #         {'name': 'Analytics Dashboard', 'icon': '📊'},
    #         {'name': 'Inventory Manager', 'icon': '📦'},
    #         {'name': 'CRM Suite', 'icon': '🤝'},
    #     ]
    #     return context

#
# class DashboardView(LoginRequiredMixin, TemplateView):
#     template_name = 'dashboard_old.html'
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         current_tenant = self.request.tenant
#
#         # 1. ACTIVE APPS: Use the real QuerySet
#         # Template will loop over 'installed_apps'
#         context['installed_apps'] = App.objects.filter(
#             # is_active=True,
#             # assigned_tenants=current_tenant
#         )
#
#         # 2. RECOMMENDED APPS: Use the real QuerySet
#         # Template will loop over 'available_apps'
#         context['available_apps'] = App.objects.filter(
#             is_active=True
#         ).exclude(
#             assigned_tenants=current_tenant
#         )
#
#         return context
#

class ProfileView(LoginRequiredMixin, TemplateView):
    """
    A tenant-themed profile page that shows user details.
    """
    template_name = 'registration/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenant'] = self.request.tenant
        return context


@csrf_exempt
def custom_upload_function(request):
    """
    Custom upload view for django-ckeditor-5.
    Adjust permissions as needed.
    """
    if request.method == "POST" and request.FILES.get("upload"):
        # Handle file storage and return URL
        # Example logic, customize based on needs
        uploaded_file = request.FILES["upload"]
        # ... save file ...
        return JsonResponse({
            "url": settings.MEDIA_URL + uploaded_file.name
        })
    return JsonResponse({"error": "Upload failed"}, status=400)