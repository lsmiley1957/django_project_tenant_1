from django import forms
from django.core.validators import RegexValidator
# IMPORT YOUR MODELS HERE
from .models import Client, Domain

from django import forms
from django.core.validators import RegexValidator
from .models import Client, Domain


class TenantSignupForm(forms.Form):
    # Mapping to 'name' field in Client model
    company_name = forms.CharField(
        max_length=100,
        label="Company Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Acme Corp'})
    )

    # Mapping to 'schema_name' in Client model (used for the subdomain)
    subdomain = forms.CharField(
        max_length=50,
        label="Desired Subdomain",
        validators=[RegexValidator(r'^[a-z0-9]+$', "Only lowercase letters and numbers are allowed.")],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'acme'})
    )

    email = forms.EmailField(
        label="Admin Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'admin@acme.com'})
    )

    password = forms.CharField(
        label="Admin Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    # Mapping to 'plan' in Client model
    plan = forms.ChoiceField(
        label="Subscription Plan",
        choices=[('basic', 'Basic'), ('pro', 'Professional'), ('ent', 'Enterprise')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Added fields to match Client model requirements if they aren't default/auto
    on_trial = forms.BooleanField(
        required=False,
        initial=True,
        label="Start with 14-day free trial?",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_subdomain(self):
        subdomain = self.cleaned_data['subdomain'].lower()
        reserved = ['www', 'admin', 'api', 'static', 'media', 'public', 'test']

        if subdomain in reserved:
            raise forms.ValidationError("This subdomain is reserved.")

        if Client.objects.filter(schema_name=subdomain).exists():
            raise forms.ValidationError("This subdomain is already taken.")

        return subdomain