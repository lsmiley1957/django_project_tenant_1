from django.urls import path
from . import views

app_name = 'associate'

urlpatterns = [
    # --- Dashboard & Core Lists ---
    # path('', views.associate_dashboard, name='associate_dashboard'),
    # path('dashboard/', views.dashboard, name='associate_dashboard'),
    path('dashboard/', views.associate_dashboard, name='associate_dashboard'),
    path('list/', views.associate_list, name='associate_list'),
    path('directory/', views.associate_list, name='associate_directory'),  # Alternative name for same view
    path('departments/', views.department_list, name='department_list'),

    # --- Associate Profiles ---
    # Placed after 'list' but before 'reviews' detail to avoid overlapping pk matches
    path('profile/<int:pk>/', views.associate_detail, name='associate_detail'),
    # path('edit/<int:pk>/', views.associate_edit, name='associate_edit'),
    # path('delete/<int:pk>/', views.associate_delete, name='associate_delete'),

    # --- Company Policy ---
    path('policies/', views.policy_list, name='policy_list'),
    path('policies/create/', views.policy_create, name='policy_create'),
    path('policies/<int:pk>/', views.policy_detail, name='policy_detail'),
    path('policies/<int:pk>/edit/', views.policy_edit, name='policy_edit'),
    path('policies/<int:pk>/delete/', views.policy_delete, name='policy_delete'),

    # --- Performance Reviews ---
    # 1. Global Summary (All associates who have reviews)
    path('reviews/', views.all_reviews_summary, name='all_reviews_summary'),

    # 2. Specific Associate's Review List (pk is the Associate ID)
    path('reviews/associate/<int:pk>/', views.review_list, name='review_list'),

    # 3. Individual Review Actions (pk is the PerformanceReview ID)
    path('reviews/detail/<int:pk>/', views.review_detail, name='review_detail'),
    path('reviews/edit/<int:pk>/', views.review_edit, name='review_edit'),
    path('reviews/delete/<int:pk>/', views.review_delete, name='review_delete'),

    # --- AJAX Handlers ---
    path('ajax/create-review/', views.ajax_create_review, name='ajax_create_review'),





    # Main Editor Interface - now pointing to the nested editor/index
    path('editor/', views.editor_view, name='document_editor'),
    path('editor/02', views.editor_view, name='document_editor_02'),
    path('templates/manage/', views.template_library_manager, name='template_manager'),

    # Performance Review Route
    # This URL 'performance_review.html' is what the iframe in index.html looks for
    # path('editor/performance_review', views.performance_review_view, name='performance_review'),
    path('editor/performance_review', views.performance_review_view, name='performance_review'),

# The endpoint requested by index.html for the dashboard table
    path('api/reviews/', views.api_get_all_performance_reviews, name='api_all_reviews'),
    # API Endpoints for the CKEditor Template Library for Performance Reviews Docs
    path('api/templates/', views.api_get_templates, name='api_templates'),

    # ADD THIS LINE:
    path('api/performance-reviews/', views.api_get_all_performance_reviews, name='api_performance_reviews'),
    path('api/save/', views.api_save_submission, name='api_save_submission'),

]