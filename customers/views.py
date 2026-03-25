from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django_tenants.utils import schema_context
from django.utils import timezone
from datetime import timedelta
from django.db import transaction, IntegrityError, connection

import time
import sys

# Import your models and the form
from .models import Client, Domain
from .forms import TenantSignupForm

# Updated imports to match your project structure
# Ensure 'Department' is imported from the correct location
from apps.demo.small_biz.branding.models import UserAppAssignment, AppRole
from registry.models import GlobalApp, GlobalDepartment

def signup_tenant(request):
    """
    Handles tenant creation with dynamic field detection for UserAppAssignment
    to prevent crashes during migration transitions.
    """
    if request.method == 'POST':
        form = TenantSignupForm(request.POST)
        if form.is_valid():
            subdomain = form.cleaned_data['subdomain'].lower()
            target_domain = f"{subdomain}.localhost"

            try:
                # 1. PRE-CREATION CLEANUP (Atomic to prevent partial fails)
                with transaction.atomic():
                    Domain.objects.filter(domain=target_domain).delete()
                    Client.objects.filter(schema_name=subdomain).delete()

                # 2. CREATE TENANT
                # This triggers schema creation and migrations via django-tenants
                tenant = Client(
                    schema_name=subdomain,
                    name=form.cleaned_data.get('company_name', subdomain),
                    plan=form.cleaned_data.get('plan', 'basic'),
                    on_trial=True,
                    paid_until=timezone.now().date() + timedelta(days=30)
                )
                tenant.save()

                # 3. CREATE DOMAIN
                Domain.objects.get_or_create(
                    domain=target_domain,
                    tenant=tenant,
                    defaults={'is_primary': True}
                )

                # 4. TENANT-SPECIFIC DATA SETUP
                # Brief pause for DB schema propagation
                time.sleep(1)

                with schema_context(tenant.schema_name):
                    connection.ensure_connection()

                    # Create the Admin User inside the new tenant schema
                    if not User.objects.filter(username=form.cleaned_data['email']).exists():
                        user = User.objects.create_superuser(
                            username=form.cleaned_data['email'],
                            email=form.cleaned_data['email'],
                            password=form.cleaned_data['password']
                        )

                        # --- DYNAMIC FIELD DETECTION ---
                        try:
                            # Use GlobalApp and GlobalDepartment as per your imports
                            default_app = GlobalApp.objects.filter(is_active=True).first()
                            if default_app:
                                role, _ = AppRole.objects.get_or_create(name="Admin")
                                # Fixed: Using GlobalDepartment instead of undefined Department
                                dept, _ = GlobalDepartment.objects.get_or_create(name="Management")

                                field_names = [f.name for f in UserAppAssignment._meta.get_fields()]
                                assignment_data = {
                                    'user': user,
                                    'app_role': role,
                                    'department': dept
                                }

                                if 'global_app' in field_names:
                                    assignment_data['global_app'] = default_app
                                else:
                                    assignment_data['app'] = default_app

                                UserAppAssignment.objects.create(**assignment_data)
                                print(f"DEBUG: Assigned {default_app.name} to {user.email}")

                        except Exception as assignment_err:
                            print(f"WARNING: Role assignment skipped: {assignment_err}")

                request.session['new_tenant_domain'] = target_domain
                request.session['new_tenant_name'] = tenant.name
                return redirect('signup_success')

            except IntegrityError as e:
                print(f"DATABASE INTEGRITY ERROR: {str(e)}")
                form.add_error('subdomain', "This subdomain is already in use.")
            except Exception as e:
                print(f"CRITICAL ERROR DURING SIGNUP: {str(e)}")
                form.add_error(None, f"System Error: {e}")
    else:
        form = TenantSignupForm()

    return render(request, 'signup.html', {'form': form})


def signup_success(request):
    """
    Success page displaying the new tenant URL.
    """
    domain = request.session.get('new_tenant_domain')
    company_name = request.session.get('new_tenant_name', 'Your Workspace')

    if not domain:
        return redirect('home')

    # Construct the full URL (port 8000 for local dev)
    # tenant_url = f"http://{domain}:8000/admin/"
    tenant_url = f"http://{domain}:8000/"

    return render(request, 'signup_success.html', {
        'tenant_url': tenant_url,
        'company_name': company_name,
        'domain': domain
    })