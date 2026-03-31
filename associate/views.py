# from email._policybase import Policy
import json
import secrets
import string

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.db.models import Count, Q, Max, Avg
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_POST, require_http_methods

from .forms import AssociateCreateForm, PerformanceReviewForm, CompanyPolicyForm
from django.contrib import messages
from datetime import timedelta
from django.utils.text import slugify
from django.utils import timezone
from .models import Associate, Department, Position, EmploymentStatus, WorkLocation, PayBand, CompanyPolicy, \
    SalaryHistory, PerformanceReview, CompanyPolicy, TemplateCategory
from .models import CKTemplate, UserSubmission


def generate_secure_password(length=12):
    """Fallback password generator to bypass missing UserManager attributes."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@login_required
def associate_dashboard(request):
    """
    Main HCM overview with full Create/Update/Delete support.
    Bypasses UserManager.make_random_password entirely using python secrets.
    """
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == "POST":
        action = request.POST.get('action')

        if action in ['create_associate', 'update_associate']:
            try:
                with transaction.atomic():
                    email = request.POST.get('email')
                    first_name = request.POST.get('first_name')
                    last_name = request.POST.get('last_name')
                    associate_pk = request.POST.get('associate_id')

                    # 1. Handle User Object
                    if action == 'create_associate':
                        if User.objects.filter(username=email).exists():
                            return JsonResponse(
                                {"status": "error", "message": "A user with this email already exists."})

                        user = User.objects.create_user(
                            username=email,
                            email=email,
                            first_name=first_name,
                            last_name=last_name
                        )
                        # FAIL-SAFE: Generate password using Python secrets module
                        # This avoids the "'UserManager' object has no attribute 'make_random_password'" error
                        random_password = generate_secure_password()
                        user.set_password(random_password)
                        user.save()

                        associate = Associate(user=user)
                    else:
                        associate = get_object_or_404(Associate, pk=associate_pk)
                        user = associate.user
                        user.first_name = first_name
                        user.last_name = last_name
                        user.email = email
                        user.username = email
                        user.save()

                    # 2. Map 28+ Fields
                    # Identity & Personal
                    associate.phone = request.POST.get('phone')
                    associate.gender = request.POST.get('gender')
                    associate.ethnicity = request.POST.get('ethnicity')
                    associate.date_of_birth = request.POST.get('date_of_birth') or None
                    if 'profile_picture' in request.FILES:
                        associate.profile_picture = request.FILES['profile_picture']

                    # Employment Structure
                    associate.department_id = request.POST.get('department') or None
                    associate.position_id = request.POST.get('position') or None
                    associate.status_id = request.POST.get('status') or None
                    associate.work_location_id = request.POST.get('work_location') or None
                    associate.pay_band_id = request.POST.get('pay_band') or None
                    associate.reports_to_id = request.POST.get('reports_to') or None

                    # Compensation & Dates
                    associate.current_salary = request.POST.get('current_salary') or 0
                    associate.hire_date = request.POST.get('hire_date') or None
                    associate.termination_date = request.POST.get('termination_date') or None

                    # Leave & PTO Management
                    associate.sick_leave_used = request.POST.get('sick_leave_used') or 0
                    associate.annual_leave_used = request.POST.get('annual_leave_used') or 0
                    associate.other_leave_used = request.POST.get('other_leave_used') or 0
                    associate.pto_accrued = request.POST.get('pto_accrued') or 0
                    associate.pto_used = request.POST.get('pto_used') or 0
                    associate.pto_balance = request.POST.get('pto_balance') or 0

                    # Emergency Contact Information
                    associate.emergency_contact_name = request.POST.get('emergency_contact_name')
                    associate.emergency_contact_phone = request.POST.get('emergency_contact_phone')
                    associate.emergency_contact_relationship = request.POST.get('emergency_contact_relationship')

                    # Address Details (ADDED/VERIFIED UPDATES)
                    associate.address = request.POST.get('address')
                    associate.address2 = request.POST.get('address2')
                    associate.city = request.POST.get('city')
                    associate.state = request.POST.get('state')
                    associate.zip = request.POST.get('zip')

                    associate.save()

                    return JsonResponse({
                        "status": "success",
                        "message": f"Successfully updated {user.get_full_name()}."
                    })

            except Exception as e:
                import traceback
                print(traceback.format_exc())
                return JsonResponse({"status": "error", "message": str(e)})

    # Standard Dashboard Data Retrieval
    associates = Associate.objects.select_related('user', 'department', 'position', 'status').all()

    context = {
        'associates': associates,
        'total_associates': associates.count(),
        'active_count': associates.filter(is_active__icontains='True').count(),
        'new_hires_month': associates.filter(hire_date__gte=timezone.now() - timezone.timedelta(days=30)).count(),

        'departments': Department.objects.all(),
        'departments_count': Department.objects.count(),
        'positions': Position.objects.all(),
        'statuses': EmploymentStatus.objects.all(),
        'statuses_count': associates.filter(status=1).count(),
        'locations': WorkLocation.objects.all(),
        'locations_count': WorkLocation.objects.count(),
        'pay_bands': PayBand.objects.all(),
        'reports_to_options': Associate.objects.select_related('user').all(),
    }

    return render(request, 'associate/dashboard.html', context)
@login_required
def associate_list(request):
    """
    Searchable directory of all associates.
    """
    query = request.GET.get('q', '')
    dept_id = request.GET.get('dept', '')
    loc_id = request.GET.get('loc', '')

    associates = Associate.objects.select_related('user', 'department', 'position', 'work_location', 'status').all()

    if query:
        # Search by name, email, or associate ID
        associates = associates.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query) |
            Q(associate_id__icontains=query)
        )

    if dept_id:
        associates = associates.filter(department_id=dept_id)

    if loc_id:
        associates = associates.filter(work_location_id=loc_id)

    context = {
        'associates': associates,
        'departments': Department.objects.all(),
        'locations': WorkLocation.objects.all(),
    }
    return render(request, 'associate/associate_list.html', context)

@login_required
def associate_detail(request, pk):
    """
    Deep dive into a specific associate.
    """
    # CRITICAL FIX: Changed Associate.select_related to Associate.objects.select_related
    associate = get_object_or_404(
        Associate.objects.select_related(
            'user',
            'department',
            'position',
            'reports_to',
            'work_location',
            'pay_band',
            'status'
        ),
        pk=pk
    )

    # Get direct reports for the org chart feature
    direct_reports = associate.direct_reports.all()

    context = {
        'associate': associate,
        'direct_reports': direct_reports,
        # Safely handle documents if the relationship exists
        'documents': associate.documents.all() if hasattr(associate, 'documents') else [],
    }
    return render(request, 'associate/associate_detail.html', context)

def policy_list(request):
    """View to list and manage company policies."""
    policies = CompanyPolicy.objects.all().order_by('-updated_at')

    if request.method == 'POST':
        policy_id = request.POST.get('policy_id')
        title = request.POST.get('title')
        category = request.POST.get('category')
        content = request.POST.get('content')

        if policy_id:
            policy = get_object_or_404(CompanyPolicy, id=policy_id)
        else:
            policy = CompanyPolicy()

        policy.title = title
        policy.category = category
        policy.content = content
        policy.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        return redirect('policy_list')

    return render(request, 'associate/policies.html', {'policies': policies})

@login_required
@permission_required('associate.add_companypolicy', raise_exception=True)
def policy_create(request):
    """View for HR/Admin to create a new company policy."""
    if request.method == 'POST':
        form = CompanyPolicyForm(request.POST)
        if form.is_valid():
            policy = form.save(commit=False)
            policy.created_by = request.user
            policy.save()
            return redirect('associate:policy_detail', pk=policy.pk)
    else:
        form = CompanyPolicyForm()
    return render(request, 'associate/policy_form.html', {'form': form, 'title': 'Create Policy'})

@login_required
def policy_detail(request, pk):
    """Detailed view of a specific policy."""
    policy = get_object_or_404(CompanyPolicy, pk=pk)
    return render(request, 'associate/policy_detail.html', {'policy': policy})

@login_required
@permission_required('associate.change_companypolicy', raise_exception=True)
def policy_edit(request, pk):
    """View to edit an existing policy."""
    policy = get_object_or_404(CompanyPolicy, pk=pk)
    if request.method == 'POST':
        form = CompanyPolicyForm(request.POST, instance=policy)
        if form.is_valid():
            form.save()
            return redirect('associate:policy_detail', pk=policy.pk)
    else:
        form = CompanyPolicyForm(instance=policy)
    return render(request, 'associate/policy_form.html', {'form': form, 'title': 'Edit Policy'})

@login_required
@permission_required('associate.delete_companypolicy', raise_exception=True)
def policy_delete(request, pk):
    """Delete a policy after confirmation."""
    policy = get_object_or_404(CompanyPolicy, pk=pk)
    if request.method == 'POST':
        policy.delete()
        return redirect('associate:policy_list')
    return render(request, 'associate/policy_confirm_delete.html', {'policy': policy})

@login_required
def all_reviews_summary(request):
    """
    Lists all associates who have reviews, showing their latest rating
    and total review count.
    """
    # Based on the error report, the relationship from Associate to
    # PerformanceReview is named 'reviews', not 'performancereview'.
    associates_with_reviews = Associate.objects.annotate(
        review_count=Count('reviews'),
        average_rating=Avg('reviews__rating'),
        latest_review_date=Max('reviews__review_date')
    ).filter(review_count__gt=0).order_by('-latest_review_date')

    context = {
        'associates': associates_with_reviews,
    }
    return render(request, 'associate/all_reviews_summary.html', context)


def associate_reviews(request, associate_id):
    """View to handle performance reviews for a specific associate."""
    associate = get_object_or_404(Associate, id=associate_id)
    reviews = PerformanceReview.objects.filter(associate=associate)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comments = request.POST.get('comments')

        PerformanceReview.objects.create(
            associate=associate,
            rating=rating,
            comments=comments,
            reviewer=request.user
        )
        return JsonResponse({'status': 'Review recorded'})

    return render(request, 'associate/reviews.html', {
        'associate': associate,
        'reviews': reviews
    })

# @login_required
# @permission_required('associate.view_performancereview', raise_exception=True)
# def review_list(request, pk=None):
#     """List reviews (usually filtered by manager or for specific associates)."""
#     associate = get_object_or_404(Associate, pk=pk)
#     reviews = PerformanceReview.objects.filter(associate=associate)
#     # reviews = PerformanceReview.objects.all().select_related('associate', 'reviewer').order_by('-review_date')
#     return render(request, 'associate/review_list.html', {'reviews': reviews, 'associate': associate,})

@login_required
def review_list(request, pk):
    """
    Displays the list of reviews for a specific associate and handles
    the creation of new reviews via AJAX/Modal.
    """
    # Use 'pk' from URL to get the specific associate being reviewed
    associate = get_object_or_404(Associate, pk=pk)
    reviews = PerformanceReview.objects.filter(associate=associate).order_by('-review_date')

    # Handle Form Submission (AJAX or POST)
    if request.method == "POST":
        form = PerformanceReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.associate = associate  # CRITICAL: Attach the associate from the URL
            review.reviewer = request.user  # Set current logged-in user as reviewer
            review.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Review saved successfully.'
                })

            messages.success(request, "Review saved successfully.")
            return redirect('associate:review_list', pk=pk)
        else:
            # If form is invalid, return errors so the frontend knows why it failed
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors.get_json_data(),
                    'message': 'Please correct the errors below.'
                }, status=400)

    # For GET requests, provide a blank form
    context = {
        'associate': associate,
        'reviews': reviews,
        'form': PerformanceReviewForm(),
        # Use associate.user to get the User object for the profile header
        'user': associate.user
    }
    return render(request, 'associate/review_list.html', context)

@login_required
@permission_required('associate.add_performancereview', raise_exception=True)
def review_create(request, associate_id):
    """Create a review for a specific associate."""
    associate = get_object_or_404(Associate, id=associate_id)
    if request.method == 'POST':
        form = PerformanceReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.associate = associate
            review.reviewer = request.user
            review.save()
            return redirect('associate:review_detail', pk=review.pk)
    else:
        form = PerformanceReviewForm()
    return render(request, 'associate/review_form.html', {'form': form, 'associate': associate})

@login_required
def review_detail(request, pk):
    """View a specific performance review."""
    review = get_object_or_404(PerformanceReview, pk=pk)
    # Ensure only the reviewer, the associate (if allowed), or HR can see this
    if request.user != review.reviewer and request.user != review.associate.user and not request.user.is_staff:
        return redirect('associate:policy_list') # Or error page
    return render(request, 'associate/review_detail.html', {'review': review})


@login_required
def review_edit(request, pk):
    # Fetch the review or return 404
    review = get_object_or_404(PerformanceReview, pk=pk)

    if request.method == "POST":
        form = PerformanceReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Review updated successfully.")
            return redirect('associate:review_detail', pk=review.pk)
    else:
        form = PerformanceReviewForm(instance=review)

    # CRITICAL: 'review' must be in this dictionary
    return render(request, 'associate/review_form.html', {
        'form': form,
        'review': review,
    })

@login_required
@permission_required('associate.delete_performancereview', raise_exception=True)
def review_delete(request, pk):
    """Delete a review."""
    review = get_object_or_404(PerformanceReview, pk=pk)
    if request.method == 'POST':
        review.delete()
        return redirect('associate:review_list')
    return render(request, 'associate/review_confirm_delete.html', {'review': review})

# --- AJAX Views ---

@login_required
@require_POST
def ajax_create_review(request):
    """Handle review submission via AJAX (e.g., from a modal)."""
    form = PerformanceReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.reviewer = request.user
        review.save()
        return JsonResponse({
            'status': 'success',
            'message': 'Review submitted successfully.',
            'review_id': review.id
        })
    return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@login_required
def department_list(request):
    """
    Management view for organizational units.
    """
    departments = Department.objects.select_related('manager__user').all()

    if request.method == "POST" and request.POST.get('action') == 'create_department':
        name = request.POST.get('name')
        code = request.POST.get('code')
        manager_id = request.POST.get('manager')

        Department.objects.create(
            name=name,
            code=code,
            manager_id=manager_id if manager_id else None
        )
        return redirect('associate:department_list')

    context = {
        'departments': departments,
        'associates': Associate.objects.all(),
    }
    return render(request, 'associate/department_list.html', context)


    # *****  CKEditor Code for Document/Forms  ******

def editor_view(request):
    """
    Main view for the Document Editor.
    """
    return render(request, 'associate/editor/index.html')


@xframe_options_exempt
def performance_review_view(request):
    """
    Serves the interactive performance review template.
    Populates dropdowns from the Associates and User models
    to match the PerformanceReview model requirements.
    """
    # 1. Pull all associates for the 'associate' field
    # associates = Associate.objects.all().select_related('position')
    associates = Associate.objects.select_related('user', 'position', 'work_location').all()

    # 2. Pull Users for the 'reviewer' field (Managers/Admins)
    # Filter by is_staff or a custom manager flag if you have one
    reviewers = User.objects.filter(is_staff=True)

    # Loads List CKEditor Templates
    templates = CKTemplate.objects.all()

    # 3. Pull rating choices from the model to keep them in sync
    rating_choices = PerformanceReview.RATING_SCALE

    context = {
        'associates': associates,
        'reviewers': reviewers,
        'templates': templates,
        'rating_choices': rating_choices,
        'status_choices': PerformanceReview.STATUS_CHOICES,
    }
    return render(request, 'associate/editor/performance_review.html', context)


def api_get_templates(request):
    """
    API Endpoint for fetching templates for the Modal library.
    Allows for category filtering.
    """
    category_id = request.GET.get('category')
    templates = CKTemplate.objects.all()

    if category_id:
        templates = templates.filter(category_id=category_id)

    data = [{
        'id': t.id,
        'title': t.title,
        'description': t.description,
        'content': t.content,
        'icon': t.category.icon if t.category else 'file',
        'category_name': t.category.name if t.category else 'Uncategorized'
    } for t in templates]

    return JsonResponse({'status': 'success', 'data_seeds': data})

# API Endpoints for Saving
def api_save_performance_review(request):
    if request.method == "POST":
        # Implementation logic to create/update PerformanceReview model instance
        # data_seeds = request.POST...
        return JsonResponse({'status': 'success', 'message': 'Review saved to database.'})
    return JsonResponse({'status': 'error'}, status=400)



# API Endpoints for Saving
def api_save_submission(request):
    """
    Handles the submission from performance_review.html.
    Renamed from api_save_performance_review to match urls.py expectations.
    """
    if request.method == "POST":
        try:
            # Extract IDs from the POST data_seeds
            associate_id = request.POST.get('associate')
            reviewer_id = request.POST.get('reviewer')

            # Validate existence of foreign keys
            if not associate_id or not reviewer_id:
                return JsonResponse({'status': 'error', 'message': 'Associate and Reviewer are required.'}, status=400)

            associate = get_object_or_404(Associate, id=associate_id)
            reviewer = get_object_or_404(User, id=reviewer_id)

            # Map form data_seeds to PerformanceReview model fields
            review = PerformanceReview.objects.create(
                associate=associate,
                reviewer=reviewer,
                status=request.POST.get('status', 'draft'),
                review_period_start=request.POST.get('review_period_start') or None,
                review_period_end=request.POST.get('review_period_end') or None,

                # Quantitative fields
                okr_summary=request.POST.get('okr_summary', ''),
                performance_rating=request.POST.get('performance_rating') or None,
                project_completion_rate=request.POST.get('project_completion_rate') or 0.00,

                # Competency ratings (default to 3 if not provided)
                leadership_rating=request.POST.get('leadership_rating', 3),
                communication_rating=request.POST.get('communication_rating', 3),
                technical_ability_rating=request.POST.get('technical_ability_rating', 3),

                # Qualitative fields
                feedback=request.POST.get('feedback', ''),
                goals_for_next_period=request.POST.get('goals_for_next_period', '')
            )

            return JsonResponse({
                'status': 'success',
                'message': f'Review for {associate.first_name} {associate.last_name} saved successfully.',
                'review_id': review.id
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)



@login_required
def api_get_all_performance_reviews(request):
    """
    Returns a list of all existing records from the PerformanceReview model.
    """
    try:
        # Fetching from the actual PerformanceReview model as requested
        reviews = PerformanceReview.objects.select_related('associate__user', 'associate__position').all().order_by(
            '-review_date')

        reviews_data = []
        for r in reviews:
            # Safely get name
            full_name = "Unknown Associate"
            if r.associate and r.associate.user:
                full_name = f"{r.associate.user.first_name} {r.associate.user.last_name}".strip() or r.associate.user.username

            # Safely get job title
            job_title = "N/A"
            if r.associate and r.associate.position:
                job_title = r.associate.position.title

            # Format the date for the "Review Period" column
            period = r.review_date.strftime("%b %Y") if r.review_date else "N/A"

            reviews_data.append({
                "id": r.id,
                "associateName": full_name,
                "associateJob": job_title,
                "reviewPeriod": period,
                "rating": str(r.performance_rating) if r.performance_rating else "N/A",
                "status": "Finalized",  # Existing records in PerformanceReview are usually considered complete
            })

        return JsonResponse({
            "status": "success",
            "reviews": reviews_data
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)


@login_required
def template_library_manager(request):
    """Renders the main Template Manager UI."""
    categories = TemplateCategory.objects.all()
    return render(request, 'associate/template_manager.html', {
        'categories': categories
    })


def api_template_list(request):
    """API: Returns all templates for the grid and the performance workspace."""
    templates = CKTemplate.objects.select_related('category').all().order_by('-updated_at')
    data = []
    for t in templates:
        data.append({
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'content': t.content,
            'category': t.category.id if t.category else None,
            'category_name': t.category.name if t.category else 'General',
            'updated_at': t.updated_at.isoformat(),
        })
    return JsonResponse({'status': 'success', 'data_seeds': data})


@require_POST
@login_required
def api_template_create(request):
    """API: Creates a new CKTemplate."""
    try:
        data = json.loads(request.body)
        category = None
        if data.get('category_id'):
            category = get_object_or_404(TemplateCategory, id=data['category_id'])

        template = CKTemplate.objects.create(
            title=data.get('title'),
            description=data.get('description', ''),
            content=data.get('content', ''),
            category=category
        )
        return JsonResponse({'status': 'success', 'id': template.id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_POST
@login_required
def api_template_update(request, pk):
    """API: Updates an existing CKTemplate."""
    template = get_object_or_404(CKTemplate, pk=pk)
    try:
        data = json.loads(request.body)
        template.title = data.get('title', template.title)
        template.description = data.get('description', template.description)
        template.content = data.get('content', template.content)

        if data.get('category_id'):
            template.category = get_object_or_404(TemplateCategory, id=data['category_id'])
        else:
            template.category = None

        template.save()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_POST
@login_required
def api_template_delete(request, pk):
    """API: Deletes a CKTemplate."""
    template = get_object_or_404(CKTemplate, pk=pk)
    template.delete()
    return JsonResponse({'status': 'success'})

@login_required
@require_http_methods(["GET", "POST"])
def api_templates(request):
    if request.method == "GET":
        templates = CKTemplate.objects.all().order_by('-created_at')
        data = [{
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "content": t.content,
            "slug": t.slug
        } for t in templates]
        return JsonResponse({"status": "success", "templates": data})

    if request.method == "POST":
        try:
            # Parse JSON body
            data = json.loads(request.body)
            title = data.get('title')
            content = data.get('content')
            description = data.get('description', '')

            if not title or not content:
                return JsonResponse({
                    "status": "error",
                    "message": "Title and Content are required."
                }, status=400)

            # Create the template
            # slugify helps prevent unique constraint errors on the SlugField
            new_template = CKTemplate.objects.create(
                title=title,
                content=content,
                description=description,
                slug=slugify(title)
            )

            return JsonResponse({
                "status": "success",
                "id": new_template.id,
                "message": "Template saved successfully"
            })

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@login_required
@require_POST
def api_save_review(request):
    """
    Saves a comprehensive performance review with numerical ratings,
    period dates, and CKEditor feedback.
    """
    try:
        data = json.loads(request.body)

        # 1. Identity Check
        associate_id = data.get('associate_id')
        if not associate_id:
            return JsonResponse({"status": "error", "message": "Associate selection is required."}, status=400)

        try:
            associate = Associate.objects.get(id=associate_id)
        except Associate.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Selected Associate not found."}, status=404)

        # 2. Data Extraction with defaults
        # We handle empty strings for dates by converting them to None
        start_date = data.get('review_period_start') or None
        end_date = data.get('review_period_end') or None

        # 3. Create the Database Record
        review = PerformanceReview.objects.create(
            associate=associate,
            reviewer=request.user,  # The currently logged-in manager

            # Status & Administrative
            status=data.get('status', 'draft'),
            review_date=timezone.now().date(),
            review_period_start=start_date,
            review_period_end=end_date,

            # Numerical Ratings
            performance_rating=data.get('performance_rating'),
            leadership_rating=data.get('leadership_rating', 3),
            communication_rating=data.get('communication_rating', 3),
            technical_ability_rating=data.get('technical_ability_rating', 3),

            # Qualitative Content
            okr_summary=data.get('okr_summary', ''),
            feedback=data.get('content', ''),  # Mapping CKEditor content to feedback field
        )

        return JsonResponse({
            "status": "success",
            "message": f"Review for {associate.user.get_full_name()} saved.",
            "review_id": review.id
        })

    except Exception as e:
        # Useful for debugging during development
        import traceback
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "message": f"Server Error: {str(e)}"}, status=500)