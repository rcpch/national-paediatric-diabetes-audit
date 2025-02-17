# python imports
import datetime
import logging

# Django imports
from django.apps import apps
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.forms import BaseModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

# RCPCH imports
from ..forms.visit_form import VisitForm
from ..general_functions import get_visit_categories, get_visit_tabs
from ..kpi_class.kpis import CalculateKPIS
from ..models import Patient, Transfer, Visit
from .mixins import (
    CheckCanCompleteQuestionnaireMixin,
    CheckCurrentAuditYearMixin,
    CheckPDUInstanceMixin,
    CheckPDUListMixin,
    LoginAndOTPRequiredMixin,
)

# Third party imports
logger = logging.getLogger(__name__)


class PatientVisitsListView(
    LoginAndOTPRequiredMixin, CheckPDUListMixin, PermissionRequiredMixin, ListView
):
    """
    The PatientVisitsListView class.

    This class is used to display a list of visits for a patient.
    Note that it is possible to view the visits for a patient that are not part of the current audit submission as they are filtered against the audit year in the session.

    Users with permission should be able to view all visits for a patient.
    Users should NOT be able to add, edit or delete visits for a patient in a submission that is not active, or that is not the current audit year/quarter.
    """

    permission_required = "npda.view_visit"
    permission_denied_message = "You do not have the appropriate permissions to access this page/feature. Contact your Coordinator for assistance."
    model = Visit
    template_name = "visits.html"

    def get_context_data(self, **kwargs):
        patient_id = self.kwargs.get("patient_id")
        context = super(PatientVisitsListView, self).get_context_data(**kwargs)
        patient = Patient.objects.get(pk=patient_id)
        submission = patient.submissions.filter(
            submission_active=True,
            audit_year=self.request.session.get("selected_audit_year"),
        ).first()
        visits = Visit.objects.filter(patient=patient).order_by("is_valid", "id")
        calculated_visits = []
        for visit in visits:
            visit_categories = get_visit_categories(instance=visit, form=None)
            calculated_visits.append({"visit": visit, "categories": visit_categories})
        context["visits"] = calculated_visits
        context["patient"] = patient
        context["submission"] = submission

        return context


class VisitCreateView(
    LoginAndOTPRequiredMixin,
    PermissionRequiredMixin,
    SuccessMessageMixin,
    CheckCurrentAuditYearMixin,
    CheckCanCompleteQuestionnaireMixin,
    CreateView,
):
    permission_required = "npda.add_visit"
    permission_denied_message = "You do not have the appropriate permissions to access this page/feature. Contact your Coordinator for assistance."
    model = Visit
    form_class = VisitForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["patient_id"] = self.kwargs["patient_id"]
        patient = Patient.objects.get(pk=self.kwargs["patient_id"])
        context["patient"] = patient
        context["title"] = "Add New Visit"
        context["form_method"] = "create"
        context["button_title"] = "Add New Visit"
        context["visit_tabs"] = get_visit_tabs(form=None)
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
        patient = get_object_or_404(Patient, pk=self.kwargs["patient_id"])
        self.object = form.save(commit=False)
        self.object.patient = patient
        self.object.errors = None
        self.object.is_valid = True
        self.object.save()

        super(VisitCreateView, self).form_valid(form)
        return HttpResponseRedirect(self.get_success_url())


class VisitUpdateView(
    LoginAndOTPRequiredMixin,
    CheckPDUInstanceMixin,
    PermissionRequiredMixin,
    CheckCurrentAuditYearMixin,
    CheckCanCompleteQuestionnaireMixin,
    UpdateView,
):
    permission_required = "npda.change_visit"
    permission_denied_message = "You do not have the appropriate permissions to access this page/feature. Contact your Coordinator for assistance."
    model = Visit
    form_class = VisitForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["patient_id"] = self.kwargs["patient_id"]
        context["nhs_number"] = context["form"].patient.nhs_number
        context["visit_id"] = self.kwargs["pk"]
        context["title"] = "Edit Visit Details"
        context["button_title"] = "Edit Visit Details"
        context["form_method"] = "update"
        context["visit_tabs"] = get_visit_tabs(form=context["form"])

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
        print("form_valid is called int he view")
        if "delete" in self.request.POST:
            return redirect(reverse("visit-delete", kwargs={"pk": self.kwargs["pk"]}))
        visit = form.save(commit=True)
        visit.errors = None
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
    LoginAndOTPRequiredMixin,
    CheckPDUInstanceMixin,
    PermissionRequiredMixin,
    SuccessMessageMixin,
    CheckCurrentAuditYearMixin,
    CheckCanCompleteQuestionnaireMixin,
    DeleteView,
):
    permission_required = "npda.delete_visit"
    permission_denied_message = "You do not have the appropriate permissions to access this page/feature. Contact your Coordinator for assistance."
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
