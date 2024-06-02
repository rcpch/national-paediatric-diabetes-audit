# python imports
import logging

# Django imports
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Case, When
from django.forms import BaseForm
from django.http.response import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.http import HttpResponse

# Third party imports
from two_factor.views.mixins import OTPRequiredMixin

from project.npda.models.npda_user import NPDAUser

# RCPCH imports
from ..models import Patient
from ..forms.patient_form import PatientForm
from .mixins import LoginAndOTPRequiredMixin

logger = logging.getLogger(__name__)


class PatientListView(LoginAndOTPRequiredMixin, ListView):
    model = Patient
    template_name = "patients.html"

    def get_queryset(self):
        """
        Return all patients with the number of errors in their visits
        Order by valid patients first, then by number of errors in visits, then by primary key
        Scope to patient only in the same organisation as the user
        """
        # filter patients to only those in the same organisation as the user
        user_pz_code = self.request.session.get("sibling_organisations").get("pz_code")
        logger.error(f"here is the pz code: {user_pz_code}")
        return (
            Patient.objects.filter(site__paediatric_diabetes_unit_pz_code=user_pz_code)
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
        user_pz_code = self.request.session.get("sibling_organisations", {}).get(
            "pz_code", None
        )
        context["pz_code"] = user_pz_code
        context["ods_code"] = self.request.user.organisation_employer
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

    def post(self, request, *args: str, **kwargs) -> HttpResponse:
        """
        Override POST method to requery the database for the list of patients if  view preference changes
        """
        if request.htmx:
            view_preference = request.POST.get("view_preference")
            user = NPDAUser.objects.get(pk=request.user.pk)
            user.view_preference = view_preference
            user.save()
            context = {
                "view_preference": user.view_preference,
                "ods_code": user.organisation_employer,
                "pz_code": request.session.get("sibling_organisations").get("pz_code"),
            }
            return render(request, "partials/view_preference.html", context=context)


class PatientCreateView(LoginAndOTPRequiredMixin, SuccessMessageMixin, CreateView):
    """
    Handle creation of new patient in audit
    """

    model = Patient
    form_class = PatientForm
    success_message = "New child record created was created successfully"
    success_url = reverse_lazy("patients")

    def get_context_data(self, **kwargs):
        pz_code = self.request.session.get("sibling_organisations", {}).get(
            "pz_code", ""
        )
        organisation_ods_code = self.request.user.organisation_employer
        context = super().get_context_data(**kwargs)
        context["title"] = f"Add New Child to {organisation_ods_code} ({pz_code})"
        context["button_title"] = "Add New Child"
        context["form_method"] = "create"
        return context

    def form_valid(self, form: BaseForm) -> HttpResponse:
        # the Patient record is therefore valid
        patient = form.save(commit=False)
        patient.is_valid = True
        patient.save()
        return super().form_valid(form)


class PatientUpdateView(LoginAndOTPRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    Handle update of patient in audit
    """

    model = Patient
    form_class = PatientForm
    success_message = "New child record updated successfully"
    success_url = reverse_lazy("patients")

    def get_context_data(self, **kwargs):
        patient = Patient.objects.get(pk=self.kwargs["pk"])
        pz_code = patient.site.paediatric_diabetes_unit_pz_code
        ods_code = patient.site.organisation_ods_code
        context = super().get_context_data(**kwargs)
        context["title"] = f"Edit Child Details in {ods_code}({pz_code})"
        context["button_title"] = "Edit Child Details"
        context["form_method"] = "update"
        context["patient_id"] = self.kwargs["pk"]
        return context

    def form_valid(self, form: BaseForm) -> HttpResponse:
        patient = form.save(commit=False)
        patient.is_valid = True
        patient.save()
        return super().form_valid(form)


class PatientDeleteView(LoginAndOTPRequiredMixin, SuccessMessageMixin, DeleteView):
    """
    Handle deletion of child from audit
    """

    model = Patient
    success_message = "Child removed from database"
    success_url = reverse_lazy("patients")
