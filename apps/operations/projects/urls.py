from django.urls import path
from .views import (
    ProjectListView, ProjectDetailView, ProjectCreateView, ProjectUpdateView, ProjectDeleteView,
    TaskCreateView, TaskUpdateView, TaskDeleteView,
    ProjectMemberCreateView, ProjectMemberUpdateView, TaskStatusUpdateView, ProjectMemberDeleteView
)

app_name = 'projects'

urlpatterns = [
    path('', ProjectListView.as_view(), name='project_list'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project_detail'),
    path('create/', ProjectCreateView.as_view(), name='project_create'),
    path('<int:pk>/update/', ProjectUpdateView.as_view(), name='project_update'),
    path('<int:pk>/delete/', ProjectDeleteView.as_view(), name='project_delete'),

    # Task URLs
    path('<int:project_pk>/tasks/create/', TaskCreateView.as_view(), name='task_create'),
    path('<int:project_pk>/tasks/<int:pk>/update/', TaskUpdateView.as_view(), name='task_update'),
    path('<int:project_pk>/tasks/<int:pk>/delete/', TaskDeleteView.as_view(), name='task_delete'),

    # Task Status & Notes (HTMX)
    path('<int:project_pk>/tasks/<int:pk>/status/', TaskStatusUpdateView.as_view(), name='task_status_update'),
    # This path would return the partial you have in Canvas
    path('<int:project_pk>/tasks/<int:pk>/status-modal/', TaskStatusUpdateView.as_view(), name='task_status_modal'),

    # Project Member URLs
    path('<int:project_pk>/members/add/', ProjectMemberCreateView.as_view(), name='member_create'),
    path('<int:project_pk>/members/<int:pk>/update/', ProjectMemberUpdateView.as_view(), name='member_update'),
    path('<int:project_pk>/members/<int:pk>/delete/', ProjectMemberDeleteView.as_view(), name='member_delete'),
]