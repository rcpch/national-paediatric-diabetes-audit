# python imports
import logging
import json
from datetime import date

# Django imports
from django.apps import apps
from django.contrib import messages
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Count, Case, When, Max, Q, F
from django.forms import BaseForm
from django.forms import BaseForm
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect, reverse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView


# Third party imports
import nhs_number

# Project imports
from project.npda.general_functions import (
    organisations_adapter,
    fetch_organisation_by_ods_code,
    retrieve_quarter_for_date,
    visit_falls_within_audit_period_Q_object,
    data_breadcrumbs,
    patient_breadcrumbs
)
from project.npda.models import (
    NPDAUser,
    Patient,
    Submission,
    AuditPeriod
)
from project.npda.models.paediatric_diabetes_unit import PaediatricDiabetesUnit

# RCPCH imports
from ..forms.patient_form import PatientForm
from .mixins import (
    CheckCanCompleteQuestionnaireMixin,
    CheckCurrentAuditYearMixin,
    LoginAndOTPRequiredMixin,
    PDUPermissionMixin,
    QuestionnaireContextMixin
)

logger = logging.getLogger(__name__)


class PatientListView(
    LoginAndOTPRequiredMixin,
    PDUPermissionMixin,
    PermissionRequiredMixin,
    QuestionnaireContextMixin,
    ListView,
):
    permission_required = "npda.view_patient"
    permission_denied_message = "You do not have the appropriate permissions to access this page/feature. Contact your Coordinator for assistance."
    model = Patient
    template_name = "patients.html"
    paginate_by = 50

    def split_search_string(self, search_string) -> [str]:
        """
        Split string at comma and return as a list
        """
        return [
            nhs_number.standardise_format(term.strip()) or term
            for term in search_string.split(",")
        ]

    def get_sort_by(self):
        sort_by_param = self.request.GET.get("sort_by")
        sort_param = self.request.GET.get("sort")

        sort_by = None

        # Check we are sorting by a fixed set of fields rather than the full Django __ notation
        # Note that sorting by sex or diabetes_type is hard as the key is an integer, not a string
        if sort_by_param in [
            "nhs_number",
            "unique_reference_number",
            "index_of_multiple_deprivation_quintile",
            "distance_from_lead_organisation",
            "date_of_birth",
        ]:
            sort_by = sort_by_param

        sort_by = f"-{sort_by}" if sort_param == "desc" else sort_by

        return sort_by

    def get_queryset(self):
        patient_queryset = super().get_queryset()

        if self.pdu.lead_organisation_geocoordinates is None:
            # we cannot make an API call for each patient  every time we load the page,
            # so we only do it if the geocoordinates are missing
            # This should have been done when the PDU was created
            paediatric_diabetes_unit_lead_organisation = fetch_organisation_by_ods_code(
                ods_code=self.pdu.lead_organisation_ods_code
            )
            self.pdu.lead_organisation_geocoordinates = Point(
                paediatric_diabetes_unit_lead_organisation["longitude"],
                paediatric_diabetes_unit_lead_organisation["latitude"],
                srid=4326,
            )
            self.pdu.save()
        
        filtered_patients = Q(
            submissions__submission_active=True,
            submissions__audit_period=self.audit_period
        )

        # filter by contents of the search bar
        search = self.request.GET.get("search-input")
        if search:
            search_terms = self.split_search_string(search)

            combined_q = Q()  # Initialize an empty Q object

            for item in search_terms:
                item_q = (
                    Q(nhs_number__icontains=item)
                    | Q(unique_reference_number__icontains=item)
                    | Q(pk__icontains=item)
                )
                combined_q |= item_q  # Combine with OR

            if combined_q:  # Check if any search terms were provided
                filtered_patients &= combined_q  # Apply the combined OR query

        filtered_patients &= Q(
            submissions__paediatric_diabetes_unit__pz_code=self.pdu.pz_code,
            submissions__paediatric_diabetes_unit__active=True
        )

        patient_queryset = patient_queryset.filter(filtered_patients)

        a_year_ago = timezone.now() - timezone.timedelta(days=365)

        this_audit_year_visits = visit_falls_within_audit_period_Q_object(
            audit_start_date=self.audit_period.start_date,
            prepend_query_path="visit",
        )

        patient_queryset = patient_queryset.annotate(
            audit_year=F("submissions__audit_period__start_date__year"),
            visit_error_count=Count(
                Case(When(this_audit_year_visits & Q(visit__is_valid=False), then=1))
            ),
            visits_this_audit_year=Count(this_audit_year_visits),
            incomplete_full_year_of_care=Case(
                When(diagnosis_date__gt=a_year_ago, then=True), default=False
            ),
            last_upload_date=Max("submissions__submission_date"),
            most_recent_visit_date=Max("visit__visit_date"),
            distance_from_lead_organisation=Distance(
                "location_wgs84",
                self.pdu.lead_organisation_geocoordinates,
            ),
        )

        sort_by = self.get_sort_by()

        if sort_by:
            patient_queryset = patient_queryset.order_by(sort_by)
        else:
            patient_queryset = patient_queryset.order_by(
                "is_valid",  # Patient model has errors
                "-visit_error_count",  # Any Visits associated to the patient have errors
                "incomplete_full_year_of_care",
            )

        return patient_queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["pdu"] = self.pdu

        context["breadcrumbs"] = [
            {
                "label": "Patient Data",
                "href": self.data_reverse("pdu-patients")
            }
        ]

        submission = None
        submission_error_count = 0

        submission = Submission.objects.get_submission_for_request(self.pdu, self.audit_period)
        last_submission = Submission.objects.get_submission_for_request(self.pdu, self.audit_period.previous_audit_period())

        if submission and submission.errors:
            submission_errors = json.loads(submission.errors)

            error_count = 0
            for errors_for_visit in submission_errors.values():
                for errors_for_field in errors_for_visit.values():
                    submission_error_count += len(errors_for_field)

        context["submission"] = submission
        context["last_submission"] = last_submission
        context["submission_valid_count"] = (
            context["paginator"].count - submission_error_count
        )
        context["submission_error_count"] = submission_error_count

        context["pz_code"] = self.pdu.pz_code
        context["audit_period"] = self.audit_period
        context["current_page"] = self.request.GET.get("page", 1)
        context["sort_by"] = self.get_sort_by()

        seen_first_error = False
        seen_first_valid = False
        seen_first_valid_incomplete_full_year = False
        seen_first_died = False

        context["search_input_list"] = self.split_search_string(
            search_string=self.request.GET.get("search-input", "")
        )

        # Add extra fields to the patient that we can't add to the query. This is ok because the queryset will be max the page size.
        for patient in context["page_obj"]:
            # Signpost the latest quarter
            if patient.most_recent_visit_date is not None:
                patient.latest_quarter = retrieve_quarter_for_date(
                    patient.most_recent_visit_date
                )

        seen_first_error = False
        seen_first_valid = False
        seen_first_valid_incomplete_full_year = False

        # Highlight the separation between categories of patients unless we are sorting by a particular field.
        # Each category could be empty.
        if not context["sort_by"]:
            for patient in context["page_obj"]:
                # Patients with records that need fixing or have visits that need fixing
                # This could include patients with an incomplete year of care
                if not patient.is_valid or patient.visit_error_count > 0:
                    if not seen_first_error:
                        patient.is_first_error = True
                        seen_first_error = True
                else:
                    if (
                        not seen_first_valid_incomplete_full_year
                        and patient.incomplete_full_year_of_care
                    ):
                        patient.is_first_valid_incomplete_full_year = True

                        seen_first_valid_incomplete_full_year = True
                        # Edge case: all the valid patients could have an incomplete year of care
                        seen_first_valid = True
                    elif not seen_first_valid:
                        patient.is_first_valid = True
                        seen_first_valid = True

        return context

    def get(self, request, *args: str, **kwargs) -> HttpResponse:
        response = super().get(request, *args, **kwargs)

        if request.htmx:
            htmx_response = render(
                request,
                "partials/patient_table.html",
                context=self.get_context_data(),
            )
            return htmx_response

        return response


class PatientCreateView(
    LoginAndOTPRequiredMixin,
    PermissionRequiredMixin,
    SuccessMessageMixin,
    PDUPermissionMixin,
    CheckCurrentAuditYearMixin,
    CheckCanCompleteQuestionnaireMixin,
    CreateView,
):
    """
    Handle creation of new patient in audit - should link the patient to the current audit year and the logged in user's PDU
    Note that patients can only be created in the current audit year
    """

    permission_required = "npda.add_patient"
    permission_denied_message = "You do not have the appropriate permissions to access this page/feature. Contact your Coordinator for assistance."
    model = Patient
    form_class = PatientForm
    success_message = "New child record created successfully"
    
    def get_success_url(self):
        return self.data_reverse("pdu-patients")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["paediatric_diabetes_unit"] = self.pdu
        kwargs["audit_period"] = self.audit_period
        # Get override_postcode from POST data if available
        if self.request.method in ('POST', 'PUT'):
            kwargs['override_postcode'] = self.request.POST.get('override_postcode', 'false') == 'true'
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = f"Add New Child to {self.pdu.lead_organisation_name}  ({self.pdu.pz_code})"
        context["title"] = title
        context["button_title"] = "Create New Child Patient Record"
        context["form_method"] = "create"
        context["override_postcode"] = False
        context["breadcrumbs"] = data_breadcrumbs(self.pdu, self.audit_period, [
            ("Patient Data", "pdu-patients"),
            ("Add patient", "pdu-patient-add"),
        ])
        return context
    
    def form_invalid(self, form):
        context = self.get_context_data()
        if "postcode" in form.errors:
            # if the postcode is invalid, we want to allow the user to save the record anyway
            if form.override_postcode:
                form.cleaned_data["override_postcode"] = True
                messages.warning(
                    self.request,
                    "The postcode you have entered is invalid. The record will be saved but please check the postcode and update it if necessary.",
                )
                form.postcode = form.cleaned_data["postcode"]
            else:
                context['button_title'] = "Save Changes with Invalid Postcode Anyway"
                context['override_postcode'] = True
                messages.error(
                    self.request,
                    "The postcode you have entered is invalid. Please check the postcode and try again.",
                )
                form.override_postcode = True
            return self.render_to_response(context)
        return super().form_invalid(form)

    def form_valid(self, form: BaseForm) -> HttpResponse:
        # the Patient record is therefore valid
        patient = form.save(commit=False)
        patient.is_valid = True
        patient.errors = None
        patient.save()

        Transfer = apps.get_model("npda", "Transfer")
        if Transfer.objects.filter(patient=patient).exists():
            # the patient is being transferred from another PDU. Update the previous_pz_code field
            transfer = Transfer.objects.get(patient=patient)
            transfer.previous_pz_code = transfer.paediatric_diabetes_unit.pz_code
            transfer.paediatric_diabetes_unit = self.pdu
            transfer.date_leaving_service = (
                form.cleaned_data.get("date_leaving_service"),
            )
            transfer.reason_leaving_service = (
                form.cleaned_data.get("reason_leaving_service"),
            )
            transfer.save()
        else:
            Transfer.objects.create(
                paediatric_diabetes_unit=self.pdu,
                patient=patient,
                date_leaving_service=None,
                reason_leaving_service=None,
            )
        # add patient to the latest audit year and the logged in user's PDU
        # the form is initialised with the current audit year

        Submission = apps.get_model("npda", "Submission")
        audit_period = self.audit_period

        submission, created = Submission.objects.update_or_create(
            audit_year=audit_period.audit_year(),
            paediatric_diabetes_unit=self.pdu,
            submission_active=True,
            defaults={
                "submission_by": NPDAUser.objects.get(pk=self.request.user.pk),
                "submission_by": NPDAUser.objects.get(pk=self.request.user.pk),
                "submission_date": timezone.now(),
                "audit_period": audit_period
            },
        )
        submission.patients.add(patient)
        submission.save()

        return super().form_valid(form)


class PatientUpdateView(
    LoginAndOTPRequiredMixin,
    PDUPermissionMixin,
    CheckCurrentAuditYearMixin,
    PermissionRequiredMixin,
    SuccessMessageMixin,
    CheckCanCompleteQuestionnaireMixin,
    UpdateView,
):
    """
    Handle update of patient in audit
    Note patients can only be updated in the current audit year
    """

    permission_required = "npda.change_patient"
    permission_denied_message = "You do not have the appropriate permissions to access this page/feature. Contact your Coordinator for assistance."
    model = Patient
    form_class = PatientForm
    success_message = "New child record updated successfully"
    Submission = apps.get_model("npda", "Submission")
    PatientSubmission = apps.get_model("npda", "PatientSubmission")

    def get_success_url(self):
        return self.data_reverse("pdu-patients")

    def get_context_data(self, **kwargs):
        Transfer = apps.get_model("npda", "Transfer")
        patient = get_object_or_404(Patient, pk=self.kwargs["pk"])
        transfer = Transfer.objects.get(patient=patient)
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Child Details"
        context["button_title"] = "Save Changes"
        context["form_method"] = "update"
        context["patient_id"] = self.kwargs["pk"]
        context["override_postcode"] = False
        context["breadcrumbs"] = patient_breadcrumbs(self.pdu, self.audit_period, patient, [])
        return context

    def form_valid(self, form: BaseForm) -> HttpResponse:
        if "delete" in self.request.POST:
            return redirect(self.data_reverse("pdu-patient-delete", kwargs={"pk": self.kwargs["pk"]}))
        patient = form.save(commit=False)
        patient.is_valid = True
        patient.errors = None
        # TODO MRB: this calls patient.save twice. super.form_valid calls it too (https://github.com/rcpch/national-paediatric-diabetes-audit/issues/335)
        patient.save()
        return super().form_valid(form)
    
    def form_invalid(self, form):
        if "delete" in self.request.POST:
            return redirect(self.data_reverse("pdu-patient-delete", kwargs={"pk": self.kwargs["pk"]}))
        context = self.get_context_data()
        if "postcode" in form.errors:
            # if the postcode is invalid, we want to allow the user to save the record anyway
            if form.override_postcode:
                form.cleaned_data["override_postcode"] = True
                messages.warning(
                    self.request,
                    "The postcode you have entered is invalid. The record will be saved but please check the postcode and update it if necessary.",
                )
                form.postcode = form.cleaned_data["postcode"]
            else:
                context['button_title'] = "Save Changes with Invalid Postcode Anyway"
                context['override_postcode'] = True
                messages.error(
                    self.request,
                    "The postcode you have entered is invalid. Please check the postcode and try again.",
                )
                form.override_postcode = True
            return self.render_to_response(context)
        return super().form_invalid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["paediatric_diabetes_unit"] = self.pdu
        kwargs["audit_period"] = self.audit_period
        # Get override_postcode from POST data if available
        if self.request.method in ('POST', 'PUT'):
            kwargs['override_postcode'] = self.request.POST.get('override_postcode', 'false') == 'true'
        return kwargs
    


class PatientDeleteView(
    LoginAndOTPRequiredMixin,
    PDUPermissionMixin,
    CheckCurrentAuditYearMixin,
    PermissionRequiredMixin,
    SuccessMessageMixin,
    CheckCanCompleteQuestionnaireMixin,
    DeleteView,
):
    """
    Handle deletion of child from audit
    """

    permission_required = "npda.delete_patient"
    permission_denied_message = "You do not have the appropriate permissions to access this page/feature. Contact your Coordinator for assistance."
    model = Patient
    success_message = "Child removed from database"
    success_url = reverse_lazy("patients")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        patient = self.get_object()

        context["breadcrumbs"] = patient_breadcrumbs(self.pdu, self.audit_period, patient, [])
        
        return context

    def get_success_url(self):
        return self.data_reverse("pdu-patients")

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            return redirect(self.data_reverse("pdu-patient-update", kwargs={"pk": self.kwargs["pk"]}))
        return super().post(request, *args, **kwargs)
