# --- Forms (crm_project/crm_app/forms.py) ---
# You need to create a forms.py file in your crm_app directory
# crm_project/crm_app/forms.py
from django import forms
from .models import Lead, Opportunity, Territory
from django.contrib.auth.models import User


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['name', 'email', 'phone', 'company', 'source', 'status', 'description', 'assigned_to', 'territory']
        widgets = {
            'close_date': forms.DateInput(attrs={'type': 'date'}),  # HTML5 date picker
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap-like classes to fields for styling
        for field_name, field in self.fields.items():
            field.widget.attrs[
                'class'] = 'form-control rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'

        # Ensure assigned_to and territory dropdowns are populated
        self.fields['assigned_to'].queryset = User.objects.all().order_by('username')
        self.fields['territory'].queryset = Territory.objects.all().order_by('name')


class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = ['lead', 'name', 'amount', 'stage', 'close_date', 'description', 'assigned_to', 'territory']
        widgets = {
            'close_date': forms.DateInput(attrs={'type': 'date'}),  # HTML5 date picker
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap-like classes to fields for styling
        for field_name, field in self.fields.items():
            field.widget.attrs[
                'class'] = 'form-control rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'

        # Ensure lead, assigned_to and territory dropdowns are populated
        self.fields['lead'].queryset = Lead.objects.all().order_by('name')
        self.fields['assigned_to'].queryset = User.objects.all().order_by('username')
        self.fields['territory'].queryset = Territory.objects.all().order_by('name')


class TerritoryForm(forms.ModelForm):
    class Meta:
        model = Territory
        fields = ['name', 'description']

