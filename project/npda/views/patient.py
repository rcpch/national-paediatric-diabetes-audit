from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Patient
from ..forms.patient_form import PatientForm


class PatientListView(LoginRequiredMixin, ListView):
    model = Patient
    template_name = "patients.html"

    def get_queryset(self):
        return Patient.objects.all().order_by("id")


class PatientCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """
    Handle creation of new patient in audit
    """

    model = Patient
    form_class = PatientForm
    success_message = "New child record created was created successfully"
    success_url = reverse_lazy("patients")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add New Child"
        context["button_title"] = "Add New Child"
        context["form_method"] = "create"
        return context


class PatientUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    Handle update of patient in audit
    """

    model = Patient
    form_class = PatientForm
    success_message = "New child record updated successfully"
    success_url = reverse_lazy("patients")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Child Details"
        context["button_title"] = "Edit Child Details"
        context["form_method"] = "update"
        context["patient_id"] = self.kwargs["pk"]
        return context

    def is_valid(self):
        return super(PatientForm, self).is_valid()


class PatientDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """
    Handle deletion of child from audit
    """

    model = Patient
    success_message = "Child removed from database"
    success_url = reverse_lazy("patients")
