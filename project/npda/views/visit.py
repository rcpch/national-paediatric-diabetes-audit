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
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.urls import reverse

# RCPCH imports
from ..forms.visit_form import VisitForm
from ..general_functions import (
    get_categories,
    get_tabs,
    visit_falls_within_audit_period_Q_object,
    data_breadcrumbs,
    patient_breadcrumbs,
)
from ..models import Patient, Transfer, Visit, AuditPeriod
from .mixins import (
    CheckCanCompleteQuestionnaireMixin,
    CheckCurrentAuditYearMixin,
    LoginAndOTPRequiredMixin,
    PDUPermissionMixin,
    QuestionnaireContextMixin,
)

# Third party imports
logger = logging.getLogger(__name__)


class PatientVisitsListView(
    LoginAndOTPRequiredMixin,
    PDUPermissionMixin,
    PermissionRequiredMixin,
    QuestionnaireContextMixin,
    ListView,
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

    def dispatch(self, request, *args, **kwargs):
        # Pull context from URL instead of defaulting to "current"
        self.audit_period_slug = kwargs.get("audit_period")
        self.pz_code = kwargs.get("pz_code")
        self.audit_period = get_object_or_404(AuditPeriod, slug=self.audit_period_slug)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PatientVisitsListView, self).get_context_data(**kwargs)
        context["audit_period"] = self.audit_period
        context["pdu"] = self.pdu
        context["pz_code"] = self.pz_code
        context["patient_id"] = self.kwargs["patient_id"]
        patient = get_object_or_404(Patient, pk=context["patient_id"])

        submission = patient.submissions.filter(
            submission_active=True,
            audit_period=self.audit_period,
        ).first()
        visits = (
            Visit.objects.filter(  # filter visits to those within the audit year
                patient=patient,
            )
            .filter(
                visit_falls_within_audit_period_Q_object(
                    audit_start_date=self.audit_period.start_date,
                    prepend_query_path=None,
                )
            )
            .order_by("is_valid", "id")
        )
        calculated_visits = []
        for visit in visits:
            visit_categories = get_categories(instance=visit, form=None, type="visit")
            calculated_visits.append({"visit": visit, "categories": visit_categories})
        context["visits"] = calculated_visits
        context["patient"] = patient
        context["submission"] = submission
        paediatric_diabetes_unit = getattr(
            submission, "paediatric_diabetes_unit", getattr(self, "pdu", None)
        )
        context["paediatric_diabetes_unit"] = paediatric_diabetes_unit

        context["breadcrumbs"] = patient_breadcrumbs(
            self.pdu,
            self.audit_period,
            patient,
            [
                {
                    "label": "Visits",
                    "href": self.data_reverse(
                        "pdu-patient-visits", kwargs={"patient_id": patient.pk}
                    ),
                }
            ],
        )

        return context


class VisitCreateView(
    LoginAndOTPRequiredMixin,
    PermissionRequiredMixin,
    SuccessMessageMixin,
    PDUPermissionMixin,
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
        context["button_title"] = "Create New Visit"
        context["visit_tabs"] = get_tabs(form=None, type="visit")
        context["override_height_weight"] = False
        context["audit_period"] = self.audit_period
        context["paediatric_diabetes_unit"] = self.pdu

        context["breadcrumbs"] = patient_breadcrumbs(
            self.pdu,
            self.audit_period,
            patient,
            [
                {
                    "label": "Visits",
                    "href": self.data_reverse(
                        "pdu-patient-visits", kwargs={"patient_id": patient.pk}
                    ),
                },
                {
                    "label": "Add visit",
                    "href": self.data_reverse(
                        "pdu-visit-create", kwargs={"patient_id": patient.pk}
                    ),
                },
            ],
        )

        return context

    def get_success_url(self):
        messages.add_message(
            self.request, messages.SUCCESS, "New visit added successfully"
        )
        return self.data_reverse(
            "pdu-patient-visits", kwargs={"patient_id": self.kwargs["patient_id"]}
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Get override_postcode from POST data if available
        # Always provide the audit_period so the form can derive dataset year
        kwargs["audit_period"] = AuditPeriod.objects.get_audit_period_for_request(
            self.request
        )

        # Pass override flag only for modifying requests
        if self.request.method in ("POST", "PUT"):
            kwargs["override_height_weight"] = (
                self.request.POST.get("override_height_weight", "false") == "true"
            )
        return kwargs

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

    def form_invalid(self, form):
        context = self.get_context_data()
        if "height" in form.errors or "weight" in form.errors:
            # if the height or weight  is invalid, we want to allow the user to save the record anyway
            if form.override_height_weight:
                form.cleaned_data["override_height_weight"] = True
                messages.warning(
                    self.request,
                    "The height or weight you have entered is invalid. The record will be saved but please check the measurement values and update it if necessary.",
                )
                form.postcode = form.cleaned_data["override_height_weight"]
            else:
                context["button_title"] = "Save Measurements Anyway"
                context["override_height_weight"] = True
                messages.error(
                    self.request,
                    "The measurement(s) you have entered are invalid. Please check the values entered and try again.",
                )
                form.override_height_weight = True
            return self.render_to_response(context)
        return super().form_invalid(form)


class VisitUpdateView(
    LoginAndOTPRequiredMixin,
    PDUPermissionMixin,
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
        context["pdu"] = self.pdu
        context["patient_id"] = self.kwargs["patient_id"]
        context["nhs_number"] = context["form"].patient.nhs_number
        context["visit_id"] = self.kwargs["pk"]
        context["title"] = "Edit/Update Visit Details"
        context["button_title"] = "Save Changes"
        context["form_method"] = "update"
        context["visit_tabs"] = get_tabs(form=context["form"], type="visit")
        visit = Visit.objects.get(pk=self.kwargs["pk"])
        context["audit_period"] = self.audit_period
        patient = visit.patient
        context["patient"] = visit.patient
        context["paediatric_diabetes_unit"] = (
            patient.submissions.first().paediatric_diabetes_unit
        )

        context["breadcrumbs"] = patient_breadcrumbs(
            self.pdu,
            self.audit_period,
            patient,
            [
                {
                    "label": "Visits",
                    "href": self.data_reverse(
                        "pdu-patient-visits", kwargs={"patient_id": patient.pk}
                    ),
                },
                {
                    "label": visit.visit_date,
                    "href": self.data_reverse(
                        "pdu-visit-update",
                        kwargs={"patient_id": patient.pk, "pk": visit.pk},
                    ),
                },
            ],
        )

        return context

    def get_success_url(self):
        messages.add_message(
            self.request, messages.SUCCESS, "Visit edited successfully"
        )
        return self.data_reverse(
            "pdu-patient-visits", kwargs={"patient_id": self.kwargs["patient_id"]}
        )

    def get_initial(self):
        initial = super().get_initial()
        patient = Patient.objects.get(pk=self.kwargs["patient_id"])
        initial["patient"] = patient
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Get override_postcode from POST data if available
        # Always pass the audit period for the form to use when rendering
        kwargs["audit_period"] = self.audit_period

        if self.request.method in ("POST", "PUT"):
            kwargs["override_height_weight"] = (
                self.request.POST.get("override_height_weight", "false") == "true"
            )
        return kwargs

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        if "delete" in self.request.POST:
            return redirect(
                self.data_reverse("pdu-visit-delete", kwargs={"pk": self.kwargs["pk"]})
            )
        visit = form.save(commit=True)
        visit.errors = None
        visit.is_valid = True
        visit.save(update_fields=["errors", "is_valid"])
        context = {"patient_id": self.kwargs["patient_id"]}
        messages.add_message(
            self.request, messages.SUCCESS, "Visit edited successfully"
        )
        return HttpResponseRedirect(
            redirect_to=self.data_reverse("pdu-patient-visits", kwargs=context)
        )

    def form_invalid(self, form):
        context = self.get_context_data()
        if "height" in form.errors or "weight" in form.errors:
            # if the height or weight  is invalid, we want to allow the user to save the record anyway
            if form.override_height_weight:
                form.cleaned_data["override_height_weight"] = True
                messages.warning(
                    self.request,
                    "The height or weight you have entered is invalid. The record will be saved but please check the measurement values and update it if necessary.",
                )
                form.postcode = form.cleaned_data["override_height_weight"]
            else:
                context["button_title"] = "Save Measurements Anyway"
                context["override_height_weight"] = True
                messages.error(
                    self.request,
                    "The measurement(s) you have entered are invalid. Please check the values entered and try again.",
                )
                form.override_height_weight = True
            return self.render_to_response(context)
        return super().form_invalid(form)


class VisitDeleteView(
    LoginAndOTPRequiredMixin,
    PDUPermissionMixin,
    PermissionRequiredMixin,
    SuccessMessageMixin,
    CheckCurrentAuditYearMixin,
    CheckCanCompleteQuestionnaireMixin,
    DeleteView,
):
    permission_required = "npda.delete_visit"
    permission_denied_message = "You do not have the appropriate permissions to access this page/feature. Contact your Coordinator for assistance."
    model = Visit
    success_message = "Visit removed successfully"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        visit = self.get_object()
        patient = visit.patient

        context["breadcrumbs"] = patient_breadcrumbs(
            self.pdu,
            self.audit_period,
            patient,
            [
                {
                    "label": "Visits",
                    "href": self.data_reverse(
                        "pdu-patient-visits", kwargs={"patient_id": patient.pk}
                    ),
                },
                {
                    "label": visit.visit_date,
                    "href": self.data_reverse(
                        "pdu-visit-update",
                        kwargs={"patient_id": patient.pk, "pk": visit.pk},
                    ),
                },
            ],
        )

        return context

    def get_success_url(self):
        messages.add_message(
            self.request, messages.SUCCESS, "Visit edited successfully"
        )
        return self.data_reverse(
            "pdu-patient-visits", kwargs={"patient_id": self.kwargs["patient_id"]}
        )

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            return redirect(
                self.data_reverse(
                    "pdu-visit-update",
                    kwargs={
                        "pk": self.kwargs["pk"],
                        "patient_id": self.kwargs["patient_id"],
                    },
                )
            )
        return super().post(request, *args, **kwargs)
