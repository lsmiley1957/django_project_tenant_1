from django import forms
from .models import Associate, PerformanceReview, CompanyPolicy


# Using a ModelForm ensures all fields from your Associate model are included
class AssociateCreateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()

    class Meta:
        model = Associate
        # List every field you want to appear in the dashboard form
        fields = [
            'department', 'position', 'reports_to', 'work_location',
            'pay_band', 'status', 'hire_date', 'termination_date',
            'is_active', 'profile_picture', 'phone', 'address',
            'emergency_contact_name', 'emergency_contact_relationship',
            'emergency_contact_phone'
        ]


class CompanyPolicyForm(forms.ModelForm):
    """
    Form for creating and updating company policies.
    """

    class Meta:
        model = CompanyPolicy
        fields = ['title', 'content', 'category', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Policy Title'}),
            'content': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Detailed policy content...'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PerformanceReviewForm(forms.ModelForm):
    """
    Form for Performance Reviews synchronized with all model fields.
    """
    class Meta:
        model = PerformanceReview
        # associate and reviewer are excluded as they are set in the view logic
        fields = [
            'review_date',
            'review_period_start',
            'review_period_end',
            'next_review_date',
            'performance_rating',
            'okr_summary',
            'kpi_metrics',
            'leadership_rating',
            'communication_rating',
            'technical_ability_rating',
            'feedback',
            'self_assessment_score',
            'self_assessment_comments',
            'peer_feedback_summary',
            'skills_gap_analysis',
            'training_progress',
            'goals_for_next_period',
            'goals_met',
            'goals_for_next_period'
        ]

        widgets = {
            'review_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'review_period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'review_period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'goals_met': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # CKEditor5Field in the model handles the feedback widget automatically,
            # but we can style the container or other fields here.
            'goals_for_next_period': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'List specific objectives...'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("review_period_start")
        end = cleaned_data.get("review_period_end")

        if start and end and end < start:
            raise forms.ValidationError("The review period end date cannot be before the start date.")
        return cleaned_data