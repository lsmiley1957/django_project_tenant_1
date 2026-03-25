# Built with [Django App Generator](https://app-generator.dev/tools/django-generator/)

Starter generated with [Django Generator](https://app-generator.dev/tools/django-generator/) (an open-source service) using **Gradient Design**, best practices and up-to-date Dependencies.
In order to use the sources, follow the build instructions as presented in `Start with Docker` and `Manual Build` sections. 

- Get [Support](https://app-generator.dev/ticket/create/?generated_repo=https://github.com/app-generator/django-gradient-1754413962) via `eMail` and `Discord`
- Resources:
  - [Getting Started with Django](https://app-generator.dev/docs/technologies/django/index.html)
  - [Onboarding Kit for Developers](https://app-generator.dev/onboarding-kit/) - Premium resources for coding services in no-time.
  - [Discounts for Developers](https://app-generator.dev/discounts) - Build your own dev bundle and start fast 
  - [Build Dynamic Services with Django](https://app-generator.dev/docs/developer-tools/dynamic-django/index.html)
  
<br />

## Features: 

- `Up-to-date Dependencies`, Best practices
- Desing: Gradient
- Extended User Profile 
- (optional) API Generator
- (optional) Celery
- (optional) OAuth Github, Google
- (optional) CI/CD for Render
- (optional) Docker

<br />

## [Deploy on Render](https://app-generator.dev/docs/deployment/render/index.html) (free plan)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

<br /> 

## [Start Project with Docker](https://app-generator.dev/docs/technologies/docker/index.html)

> In case the starter was built with Docker support, here is the start up CMD:

```bash
$ docker-compose up --build
```

Once the above command is finished, the new app is started on `http://localhost:5085`

<br />

## Manual Build 

> Download/Clone the sources  

```bash
$ git clone https://github.com/django-gradient-1754413962.git
$ cd django-gradient-1754413962
```

<br />

> Install modules via `VENV`  

```bash
$ virtualenv env
$ source env/bin/activate
$ pip install -r requirements.txt
```

<br />

> `Set Up Database`

```bash
$ python manage.py makemigrations
$ python manage.py migrate
```

<br />

> `Start the App`

```bash
$ python manage.py runserver
```

At this point, the app runs at `http://127.0.0.1:8000/`. 

<br />





---
Starter built with [Django App Generator](https://app-generator.dev/tools/django-generator/) - Open-source service for developers and companies.


# Start of new Documentation

# [ How the Registry and Gatekeeper Work Together ]

To build a professional SaaS or multi-app system, you need a clear separation between Data, Logic, and Enforcement.

1. The Registry (The "Source of Truth")

Location: models.py and admin.py
Purpose: This is where you store who is allowed to do what.

You define an app (e.g., "Inventory").

You define roles for that app (e.g., "Manager", "Viewer").

You assign a User to a Role.

Limitation: The Registry itself doesn't "stop" anyone from visiting a URL; it just sits in the database.

2. The Gatekeeper (The "Logic Layer")

Location: gatekeeper.py
Purpose: This is the bridge. It asks the Registry: "Does User X have permission Y for App Z?"

It translates your database records into a simple True or False.

It handles "Superuser" overrides so you don't accidentally lock yourself out of your own apps.

It provides the require_app_role decorator so you don't have to write complex queries inside your views.

3. The Views (The "Enforcement")

Location: views.py (across your 10+ apps)
Purpose: This is where the actual blocking happens.

By adding @require_app_role('inventory', ['admin']) to a view, you are telling Django: "Check the Gatekeeper before running this function."

If the Gatekeeper says False, the view is never executed, and the user gets a 403 Forbidden error.

Why this is better than just "Managing via Views"

If you managed access only in views without the Gatekeeper/Registry combo, your code would look like this in every single file:

# THE BAD WAY (Hard to maintain)
def inventory_view(request):
    assignment = UserAppAssignment.objects.filter(user=request.user, app__slug='inventory').first()
    if not assignment or assignment.role != 'admin':
        raise PermissionDenied()
    # ... code ...


With the Gatekeeper + Registry approach, it looks like this:

# THE GOOD WAY (Clean and Scalable)
@require_app_role('inventory', ['admin'])
def inventory_view(request):
    # The gatekeeper already handled the check. 
    # It even attached the role to 'request.app_role' for you!
    return render(request, 'inventory.html')


Recommendation:

Keep the Gatekeeper in your core branding or registry app. Every time you create a new app (CRM, HR, Accounting), you simply import that one decorator. If you ever decide to change how permissions work (e.g., adding a "Trial Mode"), you only have to change it in one file (gatekeeper.py) instead of 50 different views.