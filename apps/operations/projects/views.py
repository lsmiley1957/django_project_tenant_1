from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Project, Task, TASK_STATUS_CHOICES, ProjectMember, TaskNote, TimeLog
from .forms import ProjectForm, TaskForm, ProjectMemberForm



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
        task = get_object_or_404(Task, pk=pk)
        # We must ensure project_members is in context for the dropdown
        project_members = ProjectMember.objects.filter(project_id=project_pk)

        context = {
            'task': task,
            'status_choices': TASK_STATUS_CHOICES,
            'project_members': project_members,
        }
        return render(request, 'projects/task_status_modal.html', context)

    def post(self, request, project_pk, pk):
        task = get_object_or_404(Task, pk=pk)

        # 1. Update Status
        new_status = request.POST.get('status')
        if new_status:
            task.status = new_status

        # 2. Update Assignment
        member_id = request.POST.get('assigned_to')
        if member_id:
            # Safer fetch to avoid 500 if ID is invalid
            member = ProjectMember.objects.filter(id=member_id).first()
            if member:
                task.assigned_to = member
        elif 'assigned_to' in request.POST:
            task.assigned_to = None

        # Update dates and description if provided
        start_date = request.POST.get('start_date')
        due_date = request.POST.get('due_date')
        description = request.POST.get('description')

        if start_date: task.start_date = start_date
        if due_date: task.due_date = due_date
        if description is not None: task.description = description

        task.save()

        # 3. Create Task Note (History)
        note_content = request.POST.get('note')
        if note_content and note_content.strip():
            TaskNote.objects.create(
                task=task,
                user=request.user,
                content=note_content.strip()
            )

        # 4. Create Time Log
        hours = request.POST.get('hours_worked')
        if hours and float(hours) > 0:
            TimeLog.objects.create(
                task=task,
                user=request.user,
                hours=hours,
                date=timezone.now().date(),
                description=note_content if note_content else f"Updated status to {task.get_status_display()}"
            )

        # Return 204 with the trigger to refresh the background dashboard
        return HttpResponse(status=204, headers={'HX-Trigger': 'taskUpdated'})
# --- TIME LOGGING ---
class LogTimeView(View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        hours = request.POST.get('hours')
        if hours:
            TimeLog.objects.create(task=task, user=request.user, hours=hours, description=request.POST.get('description', ''))
        return redirect('projects:project_detail', pk=task.project.pk)