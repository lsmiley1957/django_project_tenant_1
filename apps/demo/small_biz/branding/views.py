from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse
from django.views.generic import TemplateView

from registry.models import GlobalApp
from .models import Branding, RegistryApp, UserAppAssignment, AppRole

from .gatekeeper import require_app_role

@require_app_role('crm', ['admin', 'manager'])
def crm_dashboard(request):
    # The user can only get here if they are a CRM Admin or Manager
    return render(request, 'crm/home.html')


def branding_dashboard(request):
    """
    Central hub for managing the organization and users.
    """
    config, _ = Branding.objects.get_or_create(id=1)
    total_users = User.objects.count()

    # Count apps that have at least one role defined
    total_apps = RegistryApp.objects.count()
    total_roles = AppRole.objects.count()

    # Get the actual app objects to display on the dashboard cards
    available_apps = RegistryApp.objects.prefetch_related('roles').all()

    return render(request, 'branding/branding_dashboard.html', {
        'config': config,
        'total_users': total_users,
        'total_apps': total_apps,
        'total_roles': total_roles,
        'available_apps': available_apps,
    })


def user_management_list(request):
    """
    List all users.
    Note: Prefetch related for app_assignments was removed as that model is deleted.
    """
    users = User.objects.all()
    return render(request, 'branding/user_list.html', {
        'users': users
    })


def manage_branding(request):
    """
    View to manage global company branding and financial constants.
    """
    config, created = Branding.objects.get_or_create(id=1)

    if request.method == 'POST':
        config.company_name = request.POST.get('company_name')
        config.address_line_1 = request.POST.get('address_line_1')
        config.address_line_2 = request.POST.get('address_line_2')
        config.city = request.POST.get('city')
        config.state_province = request.POST.get('state_province')
        config.postal_code = request.POST.get('postal_code')
        config.country = request.POST.get('country')
        config.phone_number = request.POST.get('phone_number')
        config.email_address = request.POST.get('email_address')
        config.website_url = request.POST.get('website_url')
        config.tax_number = request.POST.get('tax_number')
        config.default_tax_rate = request.POST.get('default_tax_rate') or 0
        config.currency_symbol = request.POST.get('currency_symbol', '$')

        # Handle file uploads for brand identity
        if request.FILES.get('logo'):
            config.logo = request.FILES.get('logo')
        if request.FILES.get('favicon'):
            config.favicon = request.FILES.get('favicon')

        config.save()
        messages.success(request, "Company branding updated successfully.")
        return redirect('branding_dashboard')

    return render(request, 'branding/manage_branding.html', {
        'config': config
    })


def manage_user_roles(request, user_id):
    """
    This view previously managed RegistryApp roles.
    Since those models were moved/deleted, this now redirects to user management
    with a message, or you can repurpose it for Django Permissions.
    """
    messages.info(request, "Application-specific role management has moved to the Marketplace.")
    return redirect('user_management_list')


def favicon_view(request):
    """
    Serves the custom favicon from the Branding model.
    """
    config = Branding.objects.filter(id=1).first()
    if config and config.favicon:
        # If using a storage backend, redirecting to the URL is most efficient
        return redirect(config.favicon.url)
    return HttpResponse(status=204)


class TeamManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'branding/manage_team.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.all().order_by('username')
        # Ensure we prefetch roles so the UI can build the dropdowns efficiently
        context['available_apps'] = RegistryApp.objects.prefetch_related('roles').all()
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')

        # 1. Handle Role Assignment to Users
        if action == 'update_user_roles':
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, id=user_id)
            selected_roles = request.POST.getlist('roles[]')

            # Clear existing and re-assign
            UserAppAssignment.objects.filter(user=user).delete()
            for role_id in selected_roles:
                if role_id:
                    role = get_object_or_404(AppRole, id=role_id)
                    UserAppAssignment.objects.create(user=user, app_role=role)

            messages.success(request, f"Updated permissions for {user.username}")

        # 2. Handle Manual App Creation (From Registry Modal)
        elif action == 'create_app':
            name = request.POST.get('app_name')
            slug = request.POST.get('app_slug')
            if name and slug:
                RegistryApp.objects.get_or_create(name=name, slug=slug)
                messages.success(request, f"App '{name}' added to registry.")

        # 3. Handle Manual Role Creation (From Registry Modal)
        elif action == 'create_role':
            app_id = request.POST.get('app_id')
            role_name = request.POST.get('role_name')
            if app_id and role_name:
                app = get_object_or_404(RegistryApp, id=app_id)
                AppRole.objects.get_or_create(app=app, role_name=role_name)
                messages.success(request, f"Role '{role_name}' added to {app.name}.")

        return redirect('manage_team')


@login_required
def marketplace(request):
    """
    The 'App Store' view accessible by tenants.
    Shows all available GlobalApps and indicates which ones the user is already assigned to.
    """
    # 1. Fetch all active apps from the Global Registry
    available_apps = GlobalApp.objects.filter(is_active=True)

    # 2. Get the current user's active assignments
    # This helps us show "Open" instead of "Install" if they already have it
    user_assignments = UserAppAssignment.objects.filter(
        user=request.user
    ).values_list('app_id', flat=True)

    branding = Branding.objects.first()

    return render(request, 'registry/marketplace.html', {
        'available_apps': available_apps,
        'user_assignments': list(user_assignments),
        'branding': branding
    })


@login_required
def install_app_shortcut(request, app_id):
    """
    A quick 'Next Step' action: Allows a user to self-assign a basic role
    from the registry to their own profile.
    """
    global_app = get_object_or_404(GlobalApp, id=app_id)

    # Simple Logic: Assign the first available role in the first department
    # as a default 'Installation' action.
    first_dept = global_app.departments.first()
    if not first_dept:
        messages.error(request, f"App {global_app.name} has no departments/roles configured.")
        return redirect('registry:marketplace')

    first_role = first_dept.roles.first()

    # Create the assignment
    UserAppAssignment.objects.get_or_create(
        user=request.user,
        app=global_app,
        app_role=first_role
    )

    messages.success(request, f"Successfully subscribed to {global_app.name}!")
    return redirect('registry:marketplace')


@login_required
def marketplace(request):
    """
    View to browse available applications that can be 'installed'
    or assigned within this tenant.
    """
    # Assuming RegistryApp holds the global list of available modules
    available_apps = RegistryApp.objects.filter(is_active=True)

    # Get IDs of apps already installed/assigned to this user to show status
    installed_app_ids = UserAppAssignment.objects.filter(
        user=request.user
    ).values_list('app_id', flat=True)

    return render(request, 'branding/marketplace.html', {
        'available_apps': available_apps,
        'installed_app_ids': list(installed_app_ids),
    })


@login_required
def install_app(request, app_id):
    """
    Action to create a local assignment/installation of a global app.
    """
    app_to_install = get_object_or_404(RegistryApp, id=app_id)

    # Logic to "Install": Create an assignment for the current user
    # (Note: In a real app, you might pick a default role here)
    assignment, created = UserAppAssignment.objects.get_or_create(
        user=request.user,
        app=app_to_install
    )

    if created:
        messages.success(request, f"Successfully installed {app_to_install.name}!")
    else:
        messages.info(request, f"{app_to_install.name} is already installed.")

    return redirect('branding:marketplace')