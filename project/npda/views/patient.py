# python imports
from datetime import date
import logging

# Django imports
from django.apps import apps
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Case, When, Max, Q, F
from django.forms import BaseForm
from django.http.response import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.http import HttpResponse

# Third party imports
from django_htmx.http import trigger_client_event

from project.npda.general_functions.retrieve_pdu import (
    retrieve_pdu,
    retrieve_pdu_from_organisation_ods_code,
)
from project.npda.models import NPDAUser, AuditCohort

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
        pz_code = self.request.session.get("sibling_organisations").get("pz_code")
        ods_code = self.request.session.get("ods_code")
        filtered_patients = None
        # filter patients to the view preference of the user
        if self.request.user.view_preference == 0:
            # organisation view
            filtered_patients = Q(
                site__organisation_ods_code=ods_code,
            )
        elif self.request.user.view_preference == 1:
            # PDU view
            filtered_patients = Q(site__paediatric_diabetes_unit_pz_code=pz_code)
        elif self.request.user.view_preference == 2:
            # National view - no filter
            pass
        else:
            raise ValueError("Invalid view preference")

        patient_queryset = Patient.objects.filter(
            audit_cohorts__submission_active=True,
        )
        if filtered_patients is not None:
            patient_queryset = patient_queryset.filter(filtered_patients)

        return patient_queryset.annotate(
            audit_year=F("audit_cohorts__audit_year"),
            quarter=F("audit_cohorts__quarter"),
            visit_error_count=Count(Case(When(visit__is_valid=False, then=1))),
            last_upload_date=Max("audit_cohorts__submission_date"),
        ).order_by("is_valid", "visit_error_count", "pk")

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
        total_valid_patients = (
            Patient.objects.filter(audit_cohorts__submission_active=True)
            .annotate(
                visit_error_count=Count(Case(When(visit__is_valid=False, then=1))),
            )
            .order_by("is_valid", "visit_error_count", "pk")
            .filter(is_valid=True, visit_error_count__lt=1)
            .count()
        )
        context["pz_code"] = user_pz_code
        context["ods_code"] = self.request.user.organisation_employers.first().ods_code
        context["total_valid_patients"] = total_valid_patients
        context["total_invalid_patients"] = (
            Patient.objects.filter(audit_cohorts__submission_active=True).count()
            - total_valid_patients
        )
        context["index_of_first_invalid_patient"] = total_valid_patients + 1
        context["organisation_choices"] = self.request.session.get(
            "organisation_choices"
        )
        context["pdu_choices"] = self.request.session.get("pdu_choices")
        context["chosen_pdu"] = self.request.session.get("sibling_organisations").get(
            "pz_code"
        )
        return context

    def get(self, request, *args: str, **kwargs) -> HttpResponse:
        response = super().get(request, *args, **kwargs)
        if request.htmx:
            # filter the patients to only those in the same organisation as the user
            # trigger a GET request from the patient table to update the list of patients
            # by calling the get_queryset method again with the new ods_code/pz_code stored in session
            queryset = self.get_queryset()
            context = self.get_context_data()
            context["patient_list"] = queryset

            return render(
                request, "partials/patient_table.html", context=self.get_context_data()
            )
        return response

    def post(self, request, *args: str, **kwargs) -> HttpResponse:
        """
        Override POST method to requery the database for the list of patients if  view preference changes
        """
        if request.htmx:
            view_preference = request.POST.get("view_preference", None)
            ods_code = request.POST.get("patient_ods_code_select_name", None)
            pz_code = request.POST.get("patient_pz_code_select_name", None)

            if ods_code:
                # call back from the organisation select
                # retrieve the sibling organisations and store in session
                sibling_organisations = retrieve_pdu_from_organisation_ods_code(
                    ods_code=ods_code
                )
                # store the results in session
                self.request.session["sibling_organisations"] = sibling_organisations
                self.request.session["ods_code"] = ods_code
            else:
                ods_code = request.session.get("sibling_organisations")[
                    "organisations"
                ][0][
                    "ods_code"
                ]  # set the ods code to the first in the list
                self.request.session["ods_code"] = ods_code

            if pz_code:
                # call back from the PDU select
                # retrieve the sibling organisations and store in session
                sibling_organisations = retrieve_pdu(pz_number=pz_code)
                # store the results in session
                self.request.session["sibling_organisations"] = sibling_organisations

                self.request.session["organisation_choices"] = [
                    (choice["ods_code"], choice["name"])
                    for choice in sibling_organisations["organisations"]
                ]
                ods_code = request.session.get("sibling_organisations")[
                    "organisations"
                ][0][
                    "ods_code"
                ]  # set the ods code to the first in the new list
                self.request.session["ods_code"] = ods_code
            else:
                pz_code = request.session.get("sibling_organisations").get("pz_code")

            if view_preference:
                user = NPDAUser.objects.get(pk=request.user.pk)
                user.view_preference = view_preference
                user.save()
            else:
                user = NPDAUser.objects.get(pk=request.user.pk)

            context = {
                "view_preference": int(user.view_preference),
                "ods_code": ods_code,
                "pz_code": request.session.get("sibling_organisations").get("pz_code"),
                "hx_post": reverse_lazy("patients"),
                "organisation_choices": self.request.session.get(
                    "organisation_choices"
                ),
                "pdu_choices": self.request.session.get("pdu_choices"),
                "chosen_pdu": request.session.get("sibling_organisations").get(
                    "pz_code"
                ),
                "ods_code_select_name": "patient_ods_code_select_name",
                "pz_code_select_name": "patient_pz_code_select_name",
                "hx_target": "#patient_view_preference",
            }

            response = render(request, "partials/view_preference.html", context=context)

            trigger_client_event(
                response=response, name="patients", params={}
            )  # reloads the form to show the active steps
            return response


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
        # add the site to the patient record
        site = apps.get_model("npda", "Site").objects.create(
            paediatric_diabetes_unit_pz_code=self.request.session.get(
                "sibling_organisations", {}
            ).get("pz_code"),
            organisation_ods_code=self.request.user.organisation_employer,
            date_leaving_service=form.cleaned_data.get("date_leaving_service"),
            reason_leaving_service=form.cleaned_data.get("reason_leaving_service"),
        )
        patient.site = site
        patient.is_valid = True
        # add patient to the latest audit cohort
        if AuditCohort.objects.count() > 0:
            new_first = AuditCohort.objects.order_by("-submission_date").first()
            new_first.patients.add(patient)
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
