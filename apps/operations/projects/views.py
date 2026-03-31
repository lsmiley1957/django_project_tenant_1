from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Project, Task, TASK_STATUS_CHOICES, ProjectMember, TaskNote, TimeLog, TaskChecklistItem
from .forms import ProjectForm, TaskForm, ProjectMemberForm
from django.db.models import Sum


class ProjectMemberCreateView(CreateView):
    model = ProjectMember
    form_class = ProjectMemberForm
    template_name = 'projects/task_form.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Team Member'
        context['project'] = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        return context

    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        email = form.cleaned_data.get('email')
        name = form.cleaned_data.get('name')

        with transaction.atomic():
            user = None
            if email:
                user = User.objects.filter(email=email).first()
                if not user:
                    username = email.split('@')[0]
                    # Ensure unique username
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}_{counter}"
                        counter += 1

                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        first_name=name.split(' ')[0] if ' ' in name else name,
                    )
                    user.set_unusable_password()
                    user.save()

            member = form.save(commit=False)
            member.project = project
            member.user = user
            member.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.kwargs['project_pk']})



class ProjectMemberUpdateView(UpdateView):
    model = ProjectMember
    form_class = ProjectMemberForm
    template_name = 'projects/task_form.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Member'
        context['project'] = self.object.project
        return context

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.project.pk})

# --- Project Views ---
class ProjectListView(ListView):
    """
    Displays a list of all projects.
    Uses Django's generic ListView.
    """
    model = Project
    template_name = 'projects/project_list.html' # Path to the template file
    context_object_name = 'projects' # Name of the variable to use in the template


class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/project_dashboard.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add this line to provide the columns to the Kanban board
        context['status_choices'] = TASK_STATUS_CHOICES

        # Keep your existing logic for charts/JSON
        tasks = self.object.tasks.all()
        tasks_data = []
        for t in tasks:
            tasks_data.append({
                'id': str(t.id),
                'name': t.name,
                'start': t.start_date.isoformat() if t.start_date else '',
                'end': t.due_date.isoformat() if t.due_date else '',
                'progress': 100 if t.status == 'done' else (50 if t.status == 'in_progress' else 0),
                'status': t.status
            })
        import json
        context['tasks_json'] = json.dumps(tasks_data)
        return context

class ProjectCreateView(CreateView):
    """
    Handles the creation of a new project.
    Uses Django's generic CreateView.
    """
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    # Redirect to the project list after successful creation
    success_url = reverse_lazy('projects:project_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Project'
        return context

class ProjectUpdateView(UpdateView):
    """
    Handles the updating of an existing project.
    Uses Django's generic UpdateView.
    """
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    context_object_name = 'project'

    def get_success_url(self):
        """
        Redirects to the detail page of the updated project after successful update.
        """
        return reverse_lazy('project_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Project'
        return context

class ProjectDeleteView(DeleteView):
    """
    Handles the deletion of a project.
    Uses Django's generic DeleteView.
    """
    model = Project
    template_name = 'projects/confirm_delete.html' # A generic confirmation template
    success_url = reverse_lazy('projects:project_list') # Redirect to project list after deletion
    context_object_name = 'object' # The object to be deleted

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['delete_type'] = 'Project' # Used in the template for clarity
        return context

class ProjectMemberDeleteView(DeleteView):
    model = ProjectMember
    template_name = 'projects/project_confirm_delete.html'
    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.project.pk})


# --- Task Views ---

class TaskCreateView(CreateView):
    """
    Handles the creation of a new task for a specific project.
    """
    model = Task
    form_class = TaskForm
    template_name = 'projects/task_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Find the project based on the URL pk or the task's project
        if hasattr(self, 'object') and self.object:
            kwargs['project'] = self.object.project
        else:
            kwargs['project'] = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        return kwargs

    def form_valid(self, form):
        """
        Sets the project for the new task before saving.
        The project ID is retrieved from the URL kwargs.
        """
        project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        form.instance.project = project # Assign the project to the task instance
        return super().form_valid(form)

    def get_success_url(self):
        """
        Redirects to the detail page of the associated project after task creation.
        """
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.kwargs['project_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        context['title'] = f'Create New Task for {project.name}'
        context['project'] = project # Pass the project object to the template
        return context


class TaskUpdateView(UpdateView):
    """
    Handles the updating of an existing task.
    """
    model = Task
    form_class = TaskForm
    template_name = 'projects/task_form.html'
    context_object_name = 'task'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Find the project based on the URL pk or the task's project
        if hasattr(self, 'object') and self.object:
            kwargs['project'] = self.object.project
        else:
            kwargs['project'] = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        return kwargs

    def get_success_url(self):
        """
        Redirects to the detail page of the associated project after task update.
        """
        # The task object's project ID is available after the update.
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.project.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Task'
        context['project'] = self.object.project # Pass the project object to the template
        return context


# --- TASK DELETION ---
class TaskDeleteView(DeleteView):
    model = Task
    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.project.pk})

    # --- New Interactive Views ---

class ProjectDataView(View):
        """
        Returns Project Tasks as JSON for Gantt and Calendar libraries.
        """

        def get(self, request, pk):
            project = get_object_or_404(Project, pk=pk)
            tasks = project.tasks.all()

            data = []
            for task in tasks:
                data.append({
                    'id': str(task.id),
                    'name': task.name,
                    'start': project.start_date.isoformat(),  # Gantt needs start/end
                    'end': task.due_date.isoformat() if task.due_date else project.end_date.isoformat(),
                    'progress': 100 if task.status == 'done' else 0,
                    'status': task.status,
                    'description': task.description,
                })
            return JsonResponse(data, safe=False)


# --- Task Status & Notes (HTMX) ---
class TaskStatusUpdateView(View):
    def get(self, request, project_pk, pk):
        project = get_object_or_404(Project, pk=project_pk)
        task = get_object_or_404(Task, pk=pk)

        # FIX: Calculate total hours in Python to avoid TemplateSyntaxError
        total_hours = task.time_logs.aggregate(total=Sum('hours'))['total'] or 0

        context = {
            'project': project,
            'task': task,
            'status_choices': TASK_STATUS_CHOICES,
            'checklist_items': task.checklist_items.all(),
            'notes': task.notes.all().order_by('-created_at'),
            'time_logs': task.time_logs.all().order_by('-date'),
            'total_logged_hours': total_hours,  # Use this in your HTML
        }
        return render(request, 'projects/task_detail_enhanced.html', context)

    def post(self, request, project_pk, pk):
        task = get_object_or_404(Task, pk=pk)

        # 1. Update Basic Task Info & Ownership
        task.status = request.POST.get('status', task.status)

        assigned_to_id = request.POST.get('assigned_to')
        if assigned_to_id:
            task.assigned_to_id = assigned_to_id
        elif 'assigned_to' in request.POST:
            task.assigned_to = None

        # 2. Handle Checklist Deletions
        delete_ids = request.POST.getlist('delete_items')
        if delete_ids:
            task.checklist_items.filter(id__in=delete_ids).delete()

        # 3. Update Existing Checklist Items (Completion & Description Editing)
        checked_ids = request.POST.getlist('check_items')
        all_items = task.checklist_items.all()

        for item in all_items:
            # Sync completion status
            item.is_completed = (str(item.id) in checked_ids)

            # Update description if edited in the UI
            new_desc = request.POST.get(f'edit_description_{item.id}')
            if new_desc:
                item.description = new_desc.strip()
            item.save()

        # 4. Create New Checklist Items
        new_items = request.POST.getlist('bulk_new_items')
        for text_content in new_items:
            if text_content.strip():
                TaskChecklistItem.objects.create(
                    task=task,
                    description=text_content.strip(),
                    is_completed=False
                )

        # 5. Save New Note
        note_content = request.POST.get('note')
        if note_content and note_content.strip():
            TaskNote.objects.create(
                task=task,
                user=request.user if request.user.is_authenticated else None,
                content=note_content.strip()
            )

        # 6. Save Time Log
        hours = request.POST.get('hours_worked')
        if hours:
            try:
                h_val = float(hours)
                if h_val > 0:
                    TimeLog.objects.create(
                        task=task,
                        user=request.user if request.user.is_authenticated else None,
                        hours=h_val,
                        date=timezone.now().date(),
                        description="Logged via status update"
                    )
            except (ValueError, TypeError):
                pass

        task.save()
        return HttpResponse(status=204, headers={'HX-Trigger': 'taskUpdated'})


# --- TIME LOGGING ---
class LogTimeView(View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        hours = request.POST.get('hours')
        if hours:
            TimeLog.objects.create(task=task, user=request.user, hours=hours, description=request.POST.get('description', ''))
        return redirect('projects:project_detail', pk=task.project.pk)