from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


# class DashboardView(LoginRequiredMixin, TemplateView):
#     """
#     Main dashboard for the tenant, showing health metrics
#     for purchased SaaS applications.
#     """
#     template_name = 'dashboard_old.html'
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         # Mock data_seeds for SaaS Health and Purchased Apps
#         context['purchased_apps'] = [
#             {'name': 'Cloud Shield', 'status': 'Healthy', 'uptime': '99.9%', 'health_score': 98},
#             {'name': 'Data Analytics Pro', 'status': 'Warning', 'uptime': '94.2%', 'health_score': 72},
#             {'name': 'CRM Connector', 'status': 'Healthy', 'uptime': '100%', 'health_score': 100},
#         ]
#         return context

#
# class MarketplaceView(LoginRequiredMixin, TemplateView):
#     """
#     Marketplace for tenants to browse and purchase additional services.
#     """
#     template_name = 'app_catalog.html'
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         # FIXED: Added 'slug' to each dictionary to prevent NoReverseMatch in templates
#         context['available_apps'] = [
#             {
#                 'name': 'AI Predictor',
#                 'slug': 'ai-predictor',
#                 'price_start': '$49/mo',
#                 'desc': 'Predictive customer behavior modeling.'
#             },
#             {
#                 'name': 'Inventory Sync',
#                 'slug': 'inventory-sync',
#                 'price_start': '$19/mo',
#                 'desc': 'Real-time stock management across channels.'
#             },
#             {
#                 'name': 'Compliance Guard',
#                 'slug': 'compliance-guard',
#                 'price_start': '$99/mo',
#                 'desc': 'Automated audit logs and GDPR compliance.'
#             },
#         ]
#         return context
#
#
# class AppDetailView(LoginRequiredMixin, TemplateView):
#     """
#     Detailed page for a specific Marketplace App.
#     Includes Subscription Tiers, Features, Screenshots, and KB.
#     """
#     template_name = 'app_detail.html'
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         slug = self.kwargs.get('slug')
#
#         # In a real app, you would query your models: App.objects.get(slug=slug)
#         # Here is the mock data_seeds for the requested features:
#         context['app'] = {
#             'name': slug.replace('-', ' ').title(),
#             'desc': 'This high-performance module integrates directly with your existing workspace data_seeds.',
#             'features': [
#                 'Automated Data Processing',
#                 'Advanced Security Encryption',
#                 'Custom Reporting Dashboard',
#                 'Multi-user Collaboration',
#                 'API Integration Support'
#             ],
#             'screenshots': [
#                 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800',
#                 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800',
#                 'https://images.unsplash.com/photo-1543286386-713bdd548da4?w=800',
#                 'https://images.unsplash.com/photo-1551434678-e076c223a692?w=800',
#             ],
#             'tiers': [
#                 {'name': 'Starter', 'price': '49', 'features': 'Up to 5 users'},
#                 {'name': 'Professional', 'price': '149', 'features': 'Unlimited users, API access', 'featured': True},
#                 {'name': 'Enterprise', 'price': '499', 'features': 'Dedicated support, Custom SLA'},
#             ],
#             'kb_articles': [
#                 {'title': 'How to configure your first sync', 'cat': 'Setup'},
#                 {'title': 'Best practices for data_seeds security', 'cat': 'Security'},
#                 {'title': 'Troubleshooting connection errors', 'cat': 'Support'},
#             ]
#         }
#         return context