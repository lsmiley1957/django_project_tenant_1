from django.core.exceptions import PermissionDenied
from functools import wraps
from .models import UserAppAssignment, RegistryApp


class AppAccessManager:
    """
    The 'Sudo Admin' Logic.
    Handles permission checks across 10+ apps without using Django Admin.
    This acts as the central security authority for your multi-app ecosystem.
    """

    @staticmethod
    def get_user_role_for_app(user, app_slug):
        """
        Returns the role string (admin, manager, viewer) or None.
        Checks if the app is active and if the user has a valid assignment.
        """
        if not user or user.is_anonymous:
            return None

        # Superusers bypass checks for debugging/recovery
        if user.is_superuser:
            return 'admin'

        # Query the assignment through the AppRole relationship
        assignment = UserAppAssignment.objects.filter(
            user=user,
            app_role__app__slug=app_slug,
            app_role__app__is_active=True
        ).select_related('app_role', 'app_role__app').first()

        return assignment.app_role.role_name.lower() if assignment else None

    @classmethod
    def has_access(cls, user, app_slug, required_roles=None):
        """
        Check if a user can enter an app or perform a specific level of action.
        Usage: if AppAccessManager.has_access(request.user, 'crm', ['admin', 'manager']):
        """
        if not required_roles:
            # Default to basic entry if no roles specified
            required_roles = ['admin', 'manager', 'viewer', 'editor']

        user_role = cls.get_user_role_for_app(user, app_slug)
        return user_role in [role.lower() for role in required_roles]


def require_app_role(app_slug, allowed_roles=['admin', 'manager']):
    """
    A decorator for your views to restrict access at the URL level.
    Use this on your 10+ app views to ensure only authorized staff enter.

    Usage:
    @require_app_role('inventory', ['admin', 'viewer'])
    def inventory_dashboard(request):
        ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if AppAccessManager.has_access(request.user, app_slug, allowed_roles):
                # Attach the role to the request object for easy use inside the view
                request.app_role = AppAccessManager.get_user_role_for_app(request.user, app_slug)
                return view_func(request, *args, **kwargs)

            raise PermissionDenied(
                f"Access Denied: Your assigned role does not permit access to the {app_slug} module."
            )

        return _wrapped_view

    return decorator