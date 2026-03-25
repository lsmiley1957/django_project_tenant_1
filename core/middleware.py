from django.core.exceptions import PermissionDenied


class PlanAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # request.tenant is added automatically by TenantMainMiddleware
        tenant = getattr(request, 'tenant', None)

        # Example: Prevent basic users from accessing 'analytics' paths
        if request.path.startswith('/analytics/') and tenant.plan == 'basic':
            raise PermissionDenied("The Analytics dashboard requires a Premium plan.")

        return self.get_response(request)