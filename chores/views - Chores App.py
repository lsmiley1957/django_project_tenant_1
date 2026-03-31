from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum
from django.db import transaction
from .models import Parent, Child, Chore, ChoreAssignment, ComputerTime, Reward, PointTransaction


@login_required
def dashboard(request):
    """
    Main management dashboard (The 'Family Overview').
    Shows stats and contains the 'Quick Add' modals.
    """
    # 1. Identify relevant children for the logged-in user
    children = Child.objects.filter(user=request.user)
    if not children.exists():
        children = Child.objects.filter(parent__email=request.user.email)

    # Superuser/Staff fallback
    if not children.exists() and request.user.is_superuser:
        children = Child.objects.all()

    # 2. Gather Statistics for the top cards
    child_user_ids = children.values_list('user_id', flat=True)
    pending_count = ChoreAssignment.objects.filter(
        assigned_to_id__in=child_user_ids,
        status='pending'
    ).count()

    stats = {
        'total_children': children.count(),
        'pending_chores': pending_count,
        'all_parents': Parent.objects.all(),  # Used in Quick Add Parent dropdown
        'all_chores': Chore.objects.all(),  # Used in Quick Add Assignment dropdown
    }

    context = {
        'children': children,
        'stats': stats,
    }
    return render(request, 'chores/dashboard.html', context)


@login_required
def manage_data(request):
    """Handles POST requests from Quick Add modals."""
    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'child':
            name = request.POST.get('name')
            parent_id = request.POST.get('parent')
            username = request.POST.get('username')
            password = request.POST.get('password')

            parent = get_object_or_404(Parent, id=parent_id)

            try:
                # Use a transaction so if User creation fails, the Child isn't created (and vice versa)
                with transaction.atomic():
                    new_user = None
                    # Create User if username is provided
                    if username:
                        if User.objects.filter(username=username).exists():
                            messages.error(request, f"Username '{username}' is already taken.")
                            return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

                        new_user = User.objects.create_user(
                            username=username,
                            password=password if password else "password123"  # default fallback
                        )

                    # Create the Child record
                    Child.objects.create(
                        parent=parent,
                        name=name,
                        user=new_user
                    )

                    msg = f"Child '{name}' added successfully"
                    if new_user:
                        msg += f" with user account '{username}'."
                    messages.success(request, msg)

            except Exception as e:
                messages.error(request, f"Error creating child: {str(e)}")

        # ... (keep other form types: parent, chore, assign_chore as they were) ...
        elif form_type == 'parent':
            Parent.objects.create(
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                email=request.POST.get('email')
            )
            messages.success(request, "Parent added.")

    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


def chore_list(request):
    """List of all chore templates and current active assignments."""
    chores = Chore.objects.all().order_by('category', 'name')

    # Get active assignments (Pending or In Progress)
    # We use select_related to optimize the database query for child names and chore names
    active_assignments = ChoreAssignment.objects.filter(
        status__in=['pending', 'in_progress']
    ).select_related('chore', 'assigned_to').order_by('due_date')

    context = {
        'chores': chores,
        'active_assignments': active_assignments,
        # We also pass children for the 'Quick Assign' modal if you want to use it here
        'children': Child.objects.all(),
    }
    return render(request, 'chores/chore_list.html', context)


def child_detail(request, child_id):
    """Detailed view for a specific child's stats and tasks."""
    child = get_object_or_404(Child, id=child_id)

    assignments = []
    if child.user:
        assignments = ChoreAssignment.objects.filter(assigned_to=child.user).order_by('due_date')

    context = {
        'child': child,
        'assignments': assignments,
    }
    return render(request, 'chores/child_detail.html', context)


@login_required
def family_dashboard(request):
    """The 'Family Hub' view with summary cards."""
    children = Child.objects.all()

    child_summary = []
    for child in children:
        # Calculate real points earned by child's user
        points = 0
        if child.user:
            earned = PointTransaction.objects.filter(user=child.user, transaction_type='earn').aggregate(Sum('amount'))[
                         'amount__sum'] or 0
            spent = PointTransaction.objects.filter(user=child.user, transaction_type='spend').aggregate(Sum('amount'))[
                        'amount__sum'] or 0
            points = earned - spent

        child_summary.append({
            'child': child,
            'points': points,
            'tasks_count': ChoreAssignment.objects.filter(assigned_to=child.user,
                                                          status='pending').count() if child.user else 0,
            'screen_time': '0m'  # Placeholder for future computer time logic
        })

    return render(request, 'chores/family_dashboard.html', {'child_summary': child_summary})