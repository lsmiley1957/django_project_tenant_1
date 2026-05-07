from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse
from .models import GlobalApp, GlobalDepartment, GlobalRole


# --- PERMISSION HELPER ---

def is_super_admin(user):
    """Ensure only superusers can manage the global registry."""
    return user.is_superuser


# --- CLASS BASED VIEWS ---

class GlobalAppListView(ListView):
    """List all master applications available in the SaaS."""
    model = GlobalApp
    template_name = 'registry/app_list.html'
    context_object_name = 'apps'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_apps'] = GlobalApp.objects.count()
        return context


class GlobalAppDetailView(DetailView):
    """
    Detailed view of an app including its departments and roles.
    """
    model = GlobalApp
    template_name = 'registry/app_detail.html'
    # CRITICAL: This must be 'app' to match the variable used in your app_detail.html
    context_object_name = 'app'



class GlobalAppCreateView(CreateView):
    """Register a new application in the catalog."""
    model = GlobalApp
    fields = ['name', 'system_slug', 'description', 'url_conf_path', 'icon_class', 'is_premium']
    template_name = 'registry/app_form.html'
    success_url = reverse_lazy('registry:app_list')


class GlobalAppUpdateView(UpdateView):
    """Edit existing application metadata."""
    model = GlobalApp
    fields = ['name', 'system_slug', 'description', 'url_conf_path', 'icon_class', 'is_premium']
    template_name = 'registry/app_form.html'

    def get_success_url(self):
        # Redirect back to the detail page after a successful edit
        return reverse('registry:app_detail', kwargs={'pk': self.object.pk})


# --- MANAGEMENT VIEWS ---

@user_passes_test(is_super_admin)
def add_department(request, app_id):
    """Add a new department to an app via standard POST."""
    app = get_object_or_404(GlobalApp, id=app_id)
    if request.method == "POST":
        name = request.POST.get('name')
        if name:
            GlobalDepartment.objects.create(app=app, name=name)
            messages.success(request, f"Department '{name}' added to {app.name}.")
    return redirect('registry:app_detail', pk=app_id)


@user_passes_test(is_super_admin)
def quick_add_role(request, dept_id):
    """AJAX-friendly role addition."""
    dept = get_object_or_404(GlobalDepartment, id=dept_id)
    if request.method == "POST":
        name = request.POST.get('name')
        if name:
            GlobalRole.objects.create(department=dept, name=name)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'ok', 'name': name})
            messages.success(request, f"Role '{name}' added.")
    return redirect('registry:app_detail', pk=dept.app.id)


@user_passes_test(is_super_admin)
def clone_app_structure(request, app_id):
    """
    Clones the App, its Departments, and its Roles.
    """
    original_app = get_object_or_404(GlobalApp, id=app_id)
    if request.method == "POST":
        # Create a unique slug for the clone
        count = GlobalApp.objects.filter(system_slug__startswith=original_app.system_slug).count()
        new_slug = f"{original_app.system_slug}-copy-{count}"

        new_app = GlobalApp.objects.create(
            name=f"{original_app.name} (Clone)",
            system_slug=new_slug,
            description=original_app.description,
            url_conf_path=original_app.url_conf_path,
            icon_class=original_app.icon_class,
            is_premium=original_app.is_premium
        )

        for dept in original_app.departments.all():
            new_dept = GlobalDepartment.objects.create(app=new_app, name=dept.name)
            for role in dept.roles.all():
                GlobalRole.objects.create(department=new_dept, name=role.name)

        messages.success(request, f"Successfully cloned structure into '{new_app.name}'.")
        return redirect('registry:app_detail', pk=new_app.id)

    return redirect('registry:app_list')


# --- API / MANIFEST VIEWS ---

def get_registry_manifest(request):
    """
    API endpoint consumed by Tenant schemas to see what apps
    and roles are available for installation.
    """
    apps = GlobalApp.objects.filter(is_active=True)
    manifest = []

    for app in apps:
        manifest.append({
            "id": app.id,
            "slug": app.system_slug,
            "name": app.name,
            "url_conf": app.url_conf_path,
            "icon": app.icon_class,
            "departments": [
                {
                    "name": d.name,
                    "roles": [r.name for r in d.roles.all()]
                } for d in app.departments.all()
            ]
        })

    return JsonResponse({"status": "success", "apps": manifest})