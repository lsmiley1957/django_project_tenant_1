from django.urls import path
from . import views


app_name = 'chores'

urlpatterns = [
    # Main dashboard view
    path('', views.dashboard, name='dashboard'),

    # Detailed view for a specific child (e.g., /child/1/)
    path('child/<int:child_id>/', views.child_detail, name='child_detail'),

    # New Family Hub / Family Dashboard view
    path('family/', views.family_dashboard, name='family_dashboard'),

    # Data management (Handling the POST requests from modals)
    path('manage/', views.manage_data, name='manage_data'),

    # List of all available chores
    path('chores/', views.chore_list, name='chore_list'),
]