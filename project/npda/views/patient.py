# Django imports
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Case, When, Q
from django.forms import BaseForm
from django.http.response import HttpResponse
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView

# Third party imports
from two_factor.views.mixins import OTPRequiredMixin

# RCPCH imports
from ..models import Patient
from ..forms.patient_form import PatientForm


class PatientListView(LoginRequiredMixin, OTPRequiredMixin, ListView):
    model = Patient
    template_name = "patients.html"

    def get_queryset(self):
        """
        Return all patients with the number of errors in their visits
        """
        return (
            Patient.objects.all()
            .annotate(
                visit_error_count=Count(Case(When(visit__is_valid=False, then=1)))
            )
            .order_by("is_valid", "visit_error_count", "pk")
        )

    def get_context_data(self, **kwargs):
        """
        Add total number of valid and invalid patients to the context, as well as the index of the first invalid patient in the list
        Include the number of errors in each patient's visits
        Pass the context to the template
        """
        context = super().get_context_data(**kwargs)
        total_valid_patients = (
            Patient.objects.all()
            .annotate(
                visit_error_count=Count(Case(When(visit__is_valid=False, then=1)))
            )
            .order_by("is_valid", "visit_error_count", "pk")
            .filter(is_valid=True, visit_error_count__lt=1)
            .count()
        )
        context["total_valid_patients"] = total_valid_patients
        context["total_invalid_patients"] = (
            Patient.objects.all().count() - total_valid_patients
        )
        context["index_of_first_invalid_patient"] = total_valid_patients + 1
        return context


class PatientCreateView(
    LoginRequiredMixin, OTPRequiredMixin, SuccessMessageMixin, CreateView
):
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

    def form_valid(self, form: BaseForm) -> HttpResponse:
        # the Patient record is therefore valid
        patient = form.save(commit=False)
        patient.is_valid = True
        patient.save()
        return super().form_valid(form)


class PatientUpdateView(
    LoginRequiredMixin, OTPRequiredMixin, SuccessMessageMixin, UpdateView
):
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

    def form_valid(self, form: BaseForm) -> HttpResponse:
        patient = form.save(commit=False)
        patient.is_valid = True
        patient.save()
        return super().form_valid(form)


class PatientDeleteView(
    LoginRequiredMixin, OTPRequiredMixin, SuccessMessageMixin, DeleteView
):
    """
    Handle deletion of child from audit
    """

    model = Patient
    success_message = "Child removed from database"
    success_url = reverse_lazy("patients")
