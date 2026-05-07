from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView, View, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.db.models import Q
from .models import App, AppTier, AppFeature, KBArticle


# --- MIXINS ---
def handle_no_permission(self):
    """
    This is the 'Fix'. It overrides the default 403 behavior.
    """
    # CHECK: Is the user just logged out?
    if not self.request.user.is_authenticated:
        # ACTION: Redirect them to the admin login page
        login_url = reverse('admin:login')
        return redirect(f"{login_url}?next={self.request.path}")

    # CHECK: Are they logged in but simply NOT a staff member?
    # ACTION: Show the 403 error as intended for security.
    messages.error(self.request, "Access Denied: Staff permissions on the public domain required.")
    raise PermissionDenied("You do not have permission to access the Marketplace Admin.")


class GlobalAdminRequiredMixin(UserPassesTestMixin):
    """
    ULTIMATE FIX: Explicitly handles redirects to prevent 403 errors.
    If not logged in -> Redirect to Admin Login.
    If logged in but not staff -> 403 Permission Denied.
    """

    def test_func(self):
        user = self.request.user

        # 1. If user is not authenticated, they shouldn't even get a 403.
        # We return True here but handle the redirect in dispatch or
        # return False and ensure handle_no_permission is robust.
        if not user.is_authenticated:
            return False

        # 2. Global Staff Check (Your 5-10 admins)
        if user.is_staff or user.is_superuser:
            # 3. Schema Safety Check
            tenant = getattr(self.request, 'tenant', None)
            schema_name = tenant.schema_name if tenant else "None"

            # Allow on public schema or local dev domains
            if schema_name == 'public':
                return True

            host = self.request.get_host().split(':')[0]
            if host in ['localhost', '127.0.0.1']:
                return True

        return False

    def handle_no_permission(self):
        """
        Forces a redirect if the user is not logged in.
        Only raises PermissionDenied if the user IS logged in but lacks staff status.
        """
        if not self.request.user.is_authenticated:
            # Redirect to the Django Admin login page
            path = self.request.get_full_path()
            login_url = reverse('admin:login')
            return redirect(f"{login_url}?next={path}")

        # User is logged in but fails the staff/schema check
        messages.error(self.request, "Access Denied: Administrative privileges on the main domain required.")
        raise PermissionDenied("You do not have permission to access the Marketplace Admin.")


# --- 1. TENANT-FACING VIEWS ---

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'marketplace/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Safety check for tenant attribute to avoid AttributeError
        current_tenant = getattr(self.request, 'tenant', None)

        if not current_tenant:
            # If no tenant found (e.g. accessing via IP directly), show public apps only
            context['installed_apps'] = []
            context['available_apps'] = App.objects.filter(is_active=True)[:4]
            return context

        context['installed_apps'] = App.objects.filter(
            assigned_tenants=current_tenant,
            is_active=True
        )
        context['available_apps'] = App.objects.filter(
            is_active=True
        ).exclude(assigned_tenants=current_tenant)[:4]
        return context


class MarketplaceView(LoginRequiredMixin, ListView):
    """The public/tenant browser for finding new apps."""
    model = App
    template_name = 'marketplace/marketplace.html'
    context_object_name = 'apps'

    def get_queryset(self):
        queryset = App.objects.filter(is_active=True)
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(short_description__icontains=query)
            )
        return queryset


class AppDetailView(LoginRequiredMixin, DetailView):
    """Deep dive into an app with tiers and features."""
    model = App
    template_name = 'marketplace/app_detail.html'
    slug_url_kwarg = 'slug'
    context_object_name = 'app'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_tenant = getattr(self.request, 'tenant', None)
        context['is_installed'] = current_tenant in self.object.assigned_tenants.all() if current_tenant else False
        context['kb_articles'] = self.object.kb_articles.all()[:5]
        return context


class KBArticleDetailView(LoginRequiredMixin, DetailView):
    """End-user view for knowledge base articles."""
    model = KBArticle
    template_name = 'marketplace/kb_article_detail.html'
    context_object_name = 'article'


# --- 2. GLOBAL SaaS ADMIN VIEWS (App Management) ---

class AppManagementListView(GlobalAdminRequiredMixin, ListView):
    """View for managing the global app catalog."""
    model = App
    template_name = 'marketplace/admin/app_list.html'
    context_object_name = 'apps'


# ALIAS: Fixes NameError in core/urls.py and ImportError in marketplace/urls.py
# This ensures both names work regardless of which file imports them.
MarketplaceAdminListView = AppManagementListView


class AppCreateUpdateView(GlobalAdminRequiredMixin, View):
    template_name = 'marketplace/admin/app_form.html'

    def get(self, request, pk=None):
        app = get_object_or_404(App, pk=pk) if pk else None
        return render(request, self.template_name, {'app': app})

    def post(self, request, pk=None):
        app = get_object_or_404(App, pk=pk) if pk else App()

        try:
            with transaction.atomic():
                app.name = request.POST.get('name')
                app.slug = request.POST.get('slug')
                app.icon_tag = request.POST.get('icon_tag', 'box')
                app.short_description = request.POST.get('short_description')
                app.full_description = request.POST.get('full_description')
                app.is_active = request.POST.get('is_active') == 'on'
                app.save()

                # Sync Tiers
                app.tiers.all().delete()
                tier_names = request.POST.getlist('tier_name[]')
                tier_prices = request.POST.getlist('tier_price[]')
                tier_cycles = request.POST.getlist('tier_cycle[]')
                for i in range(len(tier_names)):
                    if tier_names[i].strip():
                        AppTier.objects.create(
                            app=app,
                            name=tier_names[i],
                            price=tier_prices[i] or 0,
                            billing_cycle=tier_cycles[i]
                        )

                # Sync Features
                app.features.all().delete()
                for f_text in request.POST.getlist('feature_text[]'):
                    if f_text.strip():
                        AppFeature.objects.create(app=app, feature_text=f_text)

            messages.success(request, f"App '{app.name}' saved successfully.")

            if pk:
                return redirect('app_edit', pk=app.pk)
            return redirect('marketplace_admin_list')

        except Exception as e:
            messages.error(request, f"Error saving app: {str(e)}")
            return render(request, self.template_name, {'app': app})


class AppDeleteView(GlobalAdminRequiredMixin, DeleteView):
    model = App
    success_url = reverse_lazy('marketplace_admin_list')
    template_name = 'marketplace/admin/app_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Application deleted successfully.")
        return super().delete(request, *args, **kwargs)


# --- 3. KNOWLEDGE BASE MANAGEMENT ---

class KBArticleAdminListView(GlobalAdminRequiredMixin, ListView):
    model = KBArticle
    template_name = 'marketplace/admin/kb_list.html'
    context_object_name = 'articles'


class KBArticleCreateUpdateView(GlobalAdminRequiredMixin, View):
    template_name = 'marketplace/admin/kb_form.html'

    def get(self, request, pk=None):
        article = get_object_or_404(KBArticle, pk=pk) if pk else None
        apps = App.objects.all()
        return render(request, self.template_name, {'article': article, 'apps': apps})

    def post(self, request, pk=None):
        article = get_object_or_404(KBArticle, pk=pk) if pk else KBArticle()

        try:
            app_id = request.POST.get('app')
            article.app = get_object_or_404(App, pk=app_id)
            article.title = request.POST.get('title')
            article.category = request.POST.get('category', 'General')
            article.content = request.POST.get('content')
            article.save()

            messages.success(request, "KB Article saved successfully.")
            if pk:
                return redirect('kb_edit', pk=article.pk)
            return redirect('kb_admin_list')
        except Exception as e:
            messages.error(request, f"Error saving article: {str(e)}")
            apps = App.objects.all()
            return render(request, self.template_name, {'article': article, 'apps': apps})


class KBArticleDeleteView(GlobalAdminRequiredMixin, DeleteView):
    model = KBArticle
    success_url = reverse_lazy('kb_admin_list')
    template_name = 'marketplace/admin/kb_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Article deleted successfully.")
        return super().delete(request, *args, **kwargs)