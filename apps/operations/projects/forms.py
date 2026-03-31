from django import forms
from .models import Project, Task, ProjectMember


class ProjectForm(forms.ModelForm):
    """
    Form for creating and updating Project instances.
    """
    class Meta:
        model = Project
        # Specify the fields to include in the form.
        # '__all__' includes all fields, or you can list them explicitly:
        # fields = ['name', 'description', 'start_date', 'end_date', 'status']
        fields = '__all__'
        # Add widgets for better user experience, e.g., date pickers.
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'p-2 border rounded-md w-full'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'p-2 border rounded-md w-full'}),
            'name': forms.TextInput(attrs={'class': 'p-2 border rounded-md w-full'}),
            'description': forms.Textarea(attrs={'class': 'p-2 border rounded-md w-full', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'p-2 border rounded-md w-full'}),
        }
        labels = {
            'name': 'Project Name',
            'description': 'Project Description',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'status': 'Status',
        }

class ProjectMemberForm(forms.ModelForm):
    class Meta:
        model = ProjectMember
        exclude = ['project']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'p-2 border rounded-md w-full', 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'p-2 border rounded-md w-full', 'placeholder': 'email@example.com'}),
            'role': forms.Select(attrs={'class': 'p-2 border rounded-md w-full'}),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        exclude = ['project']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'p-2 border rounded-md w-full'}),
            'name': forms.TextInput(attrs={'class': 'p-2 border rounded-md w-full'}),
            'description': forms.Textarea(attrs={'class': 'p-2 border rounded-md w-full', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'p-2 border rounded-md w-full'}),
            'assigned_to': forms.Select(attrs={'class': 'p-2 border rounded-md w-full'}),
        }

    def __init__(self, *args, **kwargs):
        # We pass the project in from the view to filter the assigned_to list
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        if project:
            self.fields['assigned_to'].queryset = ProjectMember.objects.filter(project=project)

