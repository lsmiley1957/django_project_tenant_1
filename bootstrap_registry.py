import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project_tenant_1.settings')
django.setup()

from registry.models import GlobalApp, GlobalAppRole


def bootstrap():
    print("--- Initializing Registry Data ---")

    # 1. Define your Apps
    apps_to_create = [
        {'name': 'Branding', 'slug': 'branding', 'icon_class': 'fa-paint-brush'},
        {'name': 'Point of Sale', 'slug': 'pos', 'icon_class': 'fa-shopping-cart'},
        {'name': 'Inventory', 'slug': 'inventory', 'icon_class': 'fa-boxes'},
        {'name': 'Invoicing', 'slug': 'invoicing', 'icon_class': 'fa-file-invoice-dollar'},
    ]

    for app_data in apps_to_create:
        app, created = GlobalApp.objects.get_or_create(
            slug=app_data['slug'],
            defaults={
                'name': app_data['name'],
                'icon_class': app_data['icon_class'],
                'is_active': True
            }
        )
        if created:
            print(f"Created App: {app.name}")

        # 2. Define Default Roles for each App
        roles = ['Admin', 'Manager', 'Staff']
        for role_name in roles:
            role, r_created = GlobalAppRole.objects.get_or_create(
                app=app,
                role_name=role_name
            )
            if r_created:
                print(f"  - Created Role: {role_name} for {app.name}")

    print("--- Bootstrap Complete ---")


if __name__ == "__main__":
    bootstrap()