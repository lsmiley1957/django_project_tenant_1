# crm_project/crm/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin  # Ensure user is logged in
from .models import Lead, Opportunity, Territory
from .forms import LeadForm, OpportunityForm, TerritoryForm  # We'll create these forms next


# --- Dashboard View ---
class DashboardView(LoginRequiredMixin, ListView):
    template_name = 'crm/project_dashboard.html'
    context_object_name = 'dashboard_data'  # This will be a dictionary

    def get_queryset(self):
        # This method is usually for a single model, but we need aggregated data.
        # We'll override get_context_data instead.
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get data for the current user's leads and opportunities
        user_leads = Lead.objects.filter(assigned_to=self.request.user)
        user_opportunities = Opportunity.objects.filter(assigned_to=self.request.user)

        # Aggregate data for the dashboard
        context['total_leads'] = Lead.objects.count()
        context['new_leads'] = Lead.objects.filter(status='New').count()
        context['converted_leads'] = Lead.objects.filter(status='Converted').count()
        context['total_opportunities'] = Opportunity.objects.count()
        context['closed_won_opportunities'] = Opportunity.objects.filter(stage='Closed Won').count()
        context['closed_lost_opportunities'] = Opportunity.objects.filter(stage='Closed Lost').count()
        context['total_revenue_won'] = sum(op.amount for op in Opportunity.objects.filter(stage='Closed Won'))

        # User-specific data
        context['my_total_leads'] = user_leads.count()
        context['my_new_leads'] = user_leads.filter(status='New').count()
        context['my_total_opportunities'] = user_opportunities.count()
        context['my_closed_won_opportunities'] = user_opportunities.filter(stage='Closed Won').count()
        context['my_potential_revenue'] = sum(
            op.amount for op in user_opportunities.exclude(stage__in=['Closed Won', 'Closed Lost']))

        return context


# --- Lead Views ---

class LeadListView(LoginRequiredMixin, ListView):
    model = Lead
    template_name = 'crm/lead_list.html'
    context_object_name = 'leads'
    paginate_by = 10  # Optional: Add pagination

    def get_queryset(self):
        # Filter leads to only show those assigned to the current user,
        # or all leads if the user is a superuser/staff
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Lead.objects.all()
        return Lead.objects.filter(assigned_to=self.request.user)


class LeadDetailView(LoginRequiredMixin, DetailView):
    model = Lead
    template_name = 'crm/lead_detail.html'
    context_object_name = 'lead'

    def get_queryset(self):
        # Ensure only leads assigned to the user or all for superuser/staff can be viewed
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Lead.objects.all()
        return Lead.objects.filter(assigned_to=self.request.user)


class LeadCreateView(LoginRequiredMixin, CreateView):
    model = Lead
    form_class = LeadForm  # Use our custom form
    template_name = 'crm/lead_form.html'
    success_url = reverse_lazy('crm:lead_list')  # Redirect to lead list after creation

    def form_valid(self, form):
        # Automatically assign the current user as the creator/assigned_to if not explicitly set
        if not form.instance.assigned_to:
            form.instance.assigned_to = self.request.user
        return super().form_valid(form)


class LeadUpdateView(LoginRequiredMixin, UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = 'crm/lead_form.html'
    success_url = reverse_lazy('crm:lead_list')

    def get_queryset(self):
        # Ensure only leads assigned to the user or all for superuser/staff can be updated
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Lead.objects.all()
        return Lead.objects.filter(assigned_to=self.request.user)


class LeadDeleteView(LoginRequiredMixin, DeleteView):
    model = Lead
    template_name = 'crm/lead_confirm_delete.html'  # Create a confirmation template
    success_url = reverse_lazy('crm:lead_list')

    def get_queryset(self):
        # Ensure only leads assigned to the user or all for superuser/staff can be deleted
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Lead.objects.all()
        return Lead.objects.filter(assigned_to=self.request.user)


# --- Opportunity Views ---

class OpportunityListView(LoginRequiredMixin, ListView):
    model = Opportunity
    template_name = 'crm/opportunity_list.html'
    context_object_name = 'opportunities'
    paginate_by = 10

    def get_queryset(self):
        # Filter opportunities to only show those assigned to the current user,
        # or all opportunities if the user is a superuser/staff
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Opportunity.objects.all()
        return Opportunity.objects.filter(assigned_to=self.request.user)


class OpportunityDetailView(LoginRequiredMixin, DetailView):
    model = Opportunity
    template_name = 'crm/opportunity_detail.html'
    context_object_name = 'opportunity'

    def get_queryset(self):
        # Ensure only opportunities assigned to the user or all for superuser/staff can be viewed
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Opportunity.objects.all()
        return Opportunity.objects.filter(assigned_to=self.request.user)


class OpportunityCreateView(LoginRequiredMixin, CreateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = 'crm/opportunity_form.html'
    success_url = reverse_lazy('crm:opportunity_list')

    def form_valid(self, form):
        # Automatically assign the current user as the creator/assigned_to if not explicitly set
        if not form.instance.assigned_to:
            form.instance.assigned_to = self.request.user
        return super().form_valid(form)


class OpportunityUpdateView(LoginRequiredMixin, UpdateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = 'crm/opportunity_form.html'
    success_url = reverse_lazy('crm:opportunity_list')

    def get_queryset(self):
        # Ensure only opportunities assigned to the user or all for superuser/staff can be updated
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Opportunity.objects.all()
        return Opportunity.objects.filter(assigned_to=self.request.user)


class OpportunityDeleteView(LoginRequiredMixin, DeleteView):
    model = Opportunity
    template_name = 'crm/opportunity_confirm_delete.html'
    success_url = reverse_lazy('crm:opportunity_list')

    def get_queryset(self):
        # Ensure only opportunities assigned to the user or all for superuser/staff can be deleted
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Opportunity.objects.all()
        return Opportunity.objects.filter(assigned_to=self.request.user)


# --- Territory Views ---

class TerritoryListView(LoginRequiredMixin, ListView):
    model = Territory
    template_name = 'crm/territory_list.html'
    context_object_name = 'territories'
    paginate_by = 10  # Optional: Add pagination

    def get_queryset(self):
        # Filter territories to only show those assigned to the current user,
        # or all territories if the user is a superuser/staff
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Territory.objects.all()
        return Territory.objects.filter(all)


class TerritoryDetailView(LoginRequiredMixin, DetailView):
    model = Territory
    template_name = 'crm/territory_detail.html'
    context_object_name = 'territory'

    def get_queryset(self):
        # Ensure only territorys assigned to the user or all for superuser/staff can be viewed
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Territory.objects.all()
        return Territory.objects.filter(all)


class TerritoryCreateView(LoginRequiredMixin, CreateView):
    model = Territory
    form_class = TerritoryForm  # Use our custom form
    template_name = 'crm/territory_form.html'
    success_url = reverse_lazy('crm:territory_list')  # Redirect to territory list after creation

    def form_valid(self, form):
        # Automatically assign the current user as the creator/assigned_to if not explicitly set
        if not form.instance.assigned_to:
            form.instance.assigned_to = self.request.user
        return super().form_valid(form)

class TerritoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Territory
    form_class = TerritoryForm
    template_name = 'crm/territory_form.html'
    success_url = reverse_lazy('crm:territory_list')

    def get_queryset(self):
        # Ensure only territorys assigned to the user or all for superuser/staff can be updated
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Territory.objects.all()
        return Territory.objects.filter(all)

class TerritoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Territory
    template_name = 'crm/territory_confirm_delete.html'  # Create a confirmation template
    success_url = reverse_lazy('crm:territory_list')

    def get_queryset(self):
        # Ensure only territorys assigned to the user or all for superuser/staff can be deleted
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Territory.objects.all()
        return Territory.objects.filter(all)

