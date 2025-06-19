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
from ..general_functions import (
    get_visit_categories,
    get_visit_tabs,
    visit_falls_within_audit_period_Q_object,
)
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
        audit_start_date = datetime.date(
            year=int(self.request.session.get("selected_audit_year")), month=4, day=1
        )
        submission = patient.submissions.filter(
            submission_active=True,
            audit_year=self.request.session.get("selected_audit_year"),
        ).first()
        visits = (
            Visit.objects.filter(  # filter visits to those within the audit year
                patient=patient,
            )
            .filter(
                visit_falls_within_audit_period_Q_object(
                    audit_start_date=audit_start_date, prepend_query_path=None
                )
            )
            .order_by("is_valid", "id")
        )
        calculated_visits = []
        for visit in visits:
            visit_categories = get_visit_categories(instance=visit, form=None)
            calculated_visits.append({"visit": visit, "categories": visit_categories})
        context["visits"] = calculated_visits
        context["patient"] = patient
        context["submission"] = submission
        paediatric_diabetes_unit = submission.paediatric_diabetes_unit

        context["paediatric_diabetes_unit"] = paediatric_diabetes_unit

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
        context["button_title"] = "Create New Visit"
        context["visit_tabs"] = get_visit_tabs(form=None)
        context["override_height_weight"] = False
        # Getting the PDU for the patient most of the time will be the same as the selected PDU in session.
        # However, if the user has selected a different PDU in the session but has come here from a national view
        # then we can't use that.
        if self.request.user.view_preference == 2:
            # we potentially have a choice here if the patient is in multiple PDUs
            PatientSubmission = apps.get_model("npda", "PatientSubmission")
            if (
                PatientSubmission.objects.filter(
                    patient=patient,
                    submission__audit_year=self.request.session.get(
                        "selected_audit_year"
                    ),
                    submission__submission_active=True,
                ).count()
                > 1
            ):
                # this patient has more than one active submission
                # if the user has selected a PDU in the session, we can use that
                if PatientSubmission.objects.filter(
                    patient=patient,
                    submission__audit_year=self.request.session.get(
                        "selected_audit_year"
                    ),
                    submission__submission_active=True,
                    submission__paediatric_diabetes_unit=PaediatricDiabetesUnit.objects.get(
                        pz_code=self.request.session.get("pz_code")
                    ),
                ).exists():
                    context["paediatric_diabetes_unit"] = (
                        PaediatricDiabetesUnit.objects.get(
                            pz_code=self.request.session.get("pz_code")
                        )
                    )
                else:
                    # if we can't use the PDU in the session, we shall have to use the first one
                    context["paediatric_diabetes_unit"] = (
                        PatientSubmission.objects.filter(
                            patient=patient,
                            submission__audit_year=self.request.session.get(
                                "selected_audit_year"
                            ),
                            submission__submission_active=True,
                        )
                        .first()
                        .submission.paediatric_diabetes_unit
                    )
        else:
            PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")
            context["paediatric_diabetes_unit"] = PaediatricDiabetesUnit.objects.get(
                pz_code=self.request.session.get("pz_code")
            )
        return context

    def get_success_url(self):
        messages.add_message(
            self.request, messages.SUCCESS, "New visit added successfully"
        )
        return reverse(
            "patient_visits", kwargs={"patient_id": self.kwargs["patient_id"]}
        )
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Get override_postcode from POST data if available
        if self.request.method in ('POST', 'PUT'):
            kwargs['override_height_weight'] = self.request.POST.get('override_height_weight', 'false') == 'true'
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
                context['button_title'] = "Save Measurements Anyway"
                context['override_height_weight'] = True
                messages.error(
                    self.request,
                    "The measurement(s) you have entered are invalid. Please check the values entered and try again.",
                )
                form.override_height_weight = True
            return self.render_to_response(context)
        return super().form_invalid(form)




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
        context["title"] = "Edit/Update Visit Details"
        context["button_title"] = "Save Changes"
        context["form_method"] = "update"
        context["visit_tabs"] = get_visit_tabs(form=context["form"])
        visit = Visit.objects.get(pk=self.kwargs["pk"])

        context["patient"] = visit.patient

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
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Get override_postcode from POST data if available
        if self.request.method in ('POST', 'PUT'):
            kwargs['override_height_weight'] = self.request.POST.get('override_height_weight', 'false') == 'true'
        return kwargs

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
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
                context['button_title'] = "Save Measurements Anyway"
                context['override_height_weight'] = True
                messages.error(
                    self.request,
                    "The measurement(s) you have entered are invalid. Please check the values entered and try again.",
                )
                form.override_height_weight = True
            return self.render_to_response(context)
        return super().form_invalid(form)


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

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            return redirect(
                reverse(
                    "visit-update",
                    kwargs={
                        "pk": self.kwargs["pk"],
                        "patient_id": self.kwargs["patient_id"],
                    },
                )
            )
        return super().post(request, *args, **kwargs)
