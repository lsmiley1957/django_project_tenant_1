from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView, View
from django.contrib import messages
from django.db import transaction
from .models import App, AppTier, AppFeature


# --- MIXINS ---


class GlobalAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff and self.request.tenant.schema_name == 'public'


# --- 1. TENANT-FACING VIEWS (User/Owner Dashboard) ---

class DashboardView(LoginRequiredMixin, TemplateView):
    """
    The main landing page for a tenant showing their active apps.
    """
    template_name = 'marketplace/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_tenant = self.request.tenant

        # Normal queries work now because App is a Shared App
        context['installed_apps'] = App.objects.filter(
            assigned_tenants=current_tenant,
            is_active=True
        )
        context['available_apps'] = App.objects.filter(
            is_active=True
        ).exclude(assigned_tenants=current_tenant)[:4]
        return context


class MarketplaceView(LoginRequiredMixin, ListView):
    """
    The full browser where tenants can find new apps to activate.
    """
    model = App
    template_name = 'marketplace/marketplace_list.html'
    context_object_name = 'available_apps'

    def get_queryset(self):
        return App.objects.filter(is_active=True).exclude(
            assigned_tenants=self.request.tenant
        )


class AppDetailView(LoginRequiredMixin, DetailView):
    """
    Public product page for an app.
    """
    model = App
    template_name = 'marketplace/app_detail.html'
    context_object_name = 'app'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_installed'] = self.object.assigned_tenants.filter(
            pk=self.request.tenant.pk
        ).exists()
        return context


# --- 2. GLOBAL ADMIN VIEWS (Public Schema Management) ---

class AppManagementListView(GlobalAdminRequiredMixin, ListView):
    """
    The "Admin List" view to see every app in the system (Staff Only).
    """
    model = App
    template_name = 'marketplace/app_list.html'
    context_object_name = 'apps'



class AppCreateUpdateView(GlobalAdminRequiredMixin, View):
    template_name = 'marketplace/app_form.html'

    def get(self, request, slug=None):
        app = get_object_or_404(App, slug=slug) if slug else None
        return render(request, self.template_name, {'app': app})

    def post(self, request, slug=None):
        app_id = request.POST.get('app_id')
        if slug:
            app = get_object_or_404(App, slug=slug)
        else:
            app = App()

        try:
            with transaction.atomic():
                # Basic Info
                app.name = request.POST.get('name')
                app.slug = request.POST.get('slug')
                app.short_description = request.POST.get('short_description')
                app.full_description = request.POST.get('full_description')
                app.save()

                # Dynamic Tiers
                # Note: checkboxes only send values if checked, so we handle logic carefully
                tier_names = request.POST.getlist('tier_name[]')
                tier_prices = request.POST.getlist('tier_price[]')
                tier_cycles = request.POST.getlist('tier_cycle[]')
                # For featured, we'd typically use index-based matching or a hidden field
                # but for simplicity we'll reset and recreate
                app.tiers.all().delete()
                for i in range(len(tier_names)):
                    if tier_names[i].strip():
                        AppTier.objects.create(
                            app=app,
                            name=tier_names[i],
                            price=tier_prices[i],
                            billing_cycle=tier_cycles[i]
                        )

                # Dynamic Features
                feature_texts = request.POST.getlist('feature_text[]')
                app.features.all().delete()
                for f_text in feature_texts:
                    if f_text.strip():
                        AppFeature.objects.create(app=app, feature_text=f_text)

            messages.success(request, f"Application '{app.name}' saved successfully.")
            return redirect('marketplace_admin_list')
        except Exception as e:
            messages.error(request, f"Error saving app: {str(e)}")
            return render(request, self.template_name, {'app': app})

# Add other views like MarketplaceView, AppDetailView, etc. here...