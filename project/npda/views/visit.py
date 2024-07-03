# Django imports
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.forms import BaseModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.urls import reverse_lazy, reverse

# Third party imports
from two_factor.views.mixins import OTPRequiredMixin

# RCPCH imports
from ..models import Visit, Patient
from ..forms.visit_form import VisitForm
from ..general_functions import get_visit_categories
from .mixins import LoginAndOTPRequiredMixin


class PatientVisitsListView(LoginAndOTPRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'npda.view_visit'
    model = Visit
    template_name = "visits.html"

    def get_context_data(self, **kwargs):
        patient_id = self.kwargs.get("patient_id")
        context = super(PatientVisitsListView, self).get_context_data(**kwargs)
        patient = Patient.objects.get(pk=patient_id)
        active_cohort = patient.audit_cohorts.filter(submission_active=True).first()
        visits = Visit.objects.filter(patient=patient).order_by("is_valid", "id")
        calculated_visits = []
        for visit in visits:
            visit_categories = get_visit_categories(visit)
            calculated_visits.append({"visit": visit, "categories": visit_categories})
        context["visits"] = calculated_visits
        context["patient"] = patient
        context["active_cohort"] = active_cohort
        return context


class VisitCreateView(
    LoginAndOTPRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView
):
    permission_required = "npda.add_visit"
    model = Visit
    form_class = VisitForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["patient_id"] = self.kwargs["patient_id"]
        context["title"] = "Add New Visit"
        context["form_method"] = "create"
        context["button_title"] = "Add New Visit"
        return context

    def get_success_url(self):
        messages.add_message(
            self.request, messages.SUCCESS, "New visit added successfully"
        )
        return reverse(
            "patient_visits", kwargs={"patient_id": self.kwargs["patient_id"]}
        )

    def get_initial(self):
        initial = super().get_initial()
        patient = Patient.objects.get(pk=self.kwargs["patient_id"])
        initial["patient"] = patient
        return initial

    def form_valid(self, form, **kwargs):
        self.object = form.save(commit=False)
        self.object.patient_id = self.kwargs["patient_id"]
        super(VisitCreateView, self).form_valid(form)
        return HttpResponseRedirect(self.get_success_url())


class VisitUpdateView(LoginAndOTPRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'npda.change_visit'
    model = Visit
    form_class = VisitForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        visit_instance = Visit.objects.get(pk=self.kwargs["pk"])
        visit_categories = get_visit_categories(visit_instance)
        context["visit_instance"] = visit_instance
        context["visit_errors"] = [visit_instance.errors]
        context["patient_id"] = self.kwargs["patient_id"]
        context["visit_id"] = self.kwargs["pk"]
        context["title"] = "Edit Visit Details"
        context["button_title"] = "Edit Visit Details"
        context["form_method"] = "update"
        context["visit_categories"] = visit_categories
        context["routine_measurements_categories"] = [
            "Measurements",
            "HBA1c",
            "Treatment",
            "CGM",
            "BP",
        ]
        context["annual_review_categories"] = [
            "Foot Care",
            "DECS",
            "ACR",
            "Cholesterol",
            "Thyroid",
            "Coeliac",
            "Psychology",
            "Smoking",
            "Dietician",
            "Sick Day Rules",
            "Immunisation (flu)",
        ]
        categories_with_errors = []
        categories_without_errors = []
        routine_measurements_categories_with_errors = []
        annual_review_categories_with_errors = []
        for category in visit_categories:
            if category["has_error"] == False:
                categories_without_errors.append(category["category"])
            else:
                categories_with_errors.append(category["category"])
                if category["category"] in context["routine_measurements_categories"]:
                    routine_measurements_categories_with_errors.append(
                        category["category"]
                    )
                elif category["category"] in context["annual_review_categories"]:
                    annual_review_categories_with_errors.append(category["category"])
        context["routine_measurements_categories_with_errors"] = (
            routine_measurements_categories_with_errors
        )
        context["annual_review_categories_with_errors"] = (
            annual_review_categories_with_errors
        )
        context["categories_with_errors"] = categories_with_errors
        context["categories_without_errors"] = categories_without_errors

        return context

    def get_success_url(self):
        messages.add_message(
            self.request, messages.SUCCESS, "Visit edited successfully"
        )
        return reverse(
            "patient_visits", kwargs={"patient_id": self.kwargs["patient_id"]}
        )

    def get_initial(self):
        initial = super().get_initial()
        patient = Patient.objects.get(pk=self.kwargs["patient_id"])
        initial["patient"] = patient
        return initial

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        visit = form.save(commit=True)
        visit.errors = []
        visit.is_valid = True
        visit.save(update_fields=["errors", "is_valid"])
        context = {"patient_id": self.kwargs["patient_id"]}
        messages.add_message(
            self.request, messages.SUCCESS, "Visit edited successfully"
        )
        return HttpResponseRedirect(
            redirect_to=reverse("patient_visits", kwargs=context)
        )


class VisitDeleteView(
    LoginAndOTPRequiredMixin, SuccessMessageMixin, DeleteView
):
    model = Visit
    success_url = reverse_lazy("patient_visits")
    success_message = "Visit removed successfully"

    def get_success_url(self):
        messages.add_message(
            self.request, messages.SUCCESS, "Visit edited successfully"
        )
        return reverse(
            "patient_visits", kwargs={"patient_id": self.kwargs["patient_id"]}
        )
