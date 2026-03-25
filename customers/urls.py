# urls_public.py
from django.urls import path
from customers.views import signup_tenant

urlpatterns = [
    path('signup/', signup_tenant, name='signup'),
    # ... other public urls like admin or marketing ...
]