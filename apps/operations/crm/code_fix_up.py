
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
        return Territory.objects.filter(assigned_to=self.request.user)


class TerritoryDetailView(LoginRequiredMixin, DetailView):
    model = Territory
    template_name = 'crm/territory_detail.html'
    context_object_name = 'territory'

    def get_queryset(self):
        # Ensure only territorys assigned to the user or all for superuser/staff can be viewed
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Territory.objects.all()
        return Territory.objects.filter(assigned_to=self.request.user)


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
        return Territory.objects.filter(assigned_to=self.request.user)


class TerritoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Territory
    template_name = 'crm/territory_confirm_delete.html'  # Create a confirmation template
    success_url = reverse_lazy('crm:territory_list')

    def get_queryset(self):
        # Ensure only territorys assigned to the user or all for superuser/staff can be deleted
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Territory.objects.all()
        return Territory.objects.filter(assigned_to=self.request.user)
