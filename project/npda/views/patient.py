# python imports
import logging
import json
from datetime import date

# Django imports
from django.apps import apps
from django.utils import timezone
from django.contrib import messages
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Count, Case, When, Max, Q, F
from django.forms import BaseForm
from django.forms import BaseForm
from django.http import HttpResponse
from django.http.response import HttpResponse
from django.contrib.postgres.aggregates import StringAgg
from django.shortcuts import render, redirect, reverse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.html import escape
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
    CheckPDUInstanceMixin,
    CheckPDUListMixin,
    LoginAndOTPRequiredMixin,
)
from ..general_functions.session import refresh_session_filters

logger = logging.getLogger(__name__)


class PatientListView(
    LoginAndOTPRequiredMixin,
    CheckPDUListMixin,
    PermissionRequiredMixin,
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

        PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")

        # apply filters and annotations to the queryset
        pz_code = self.request.session.get("pz_code")
        paediatric_diabetes_unit = PaediatricDiabetesUnit.objects.filter(
            pz_code=pz_code
        ).first()
        if paediatric_diabetes_unit.lead_organisation_geocoordinates is None:
            # we cannot make an API call for each patient  every time we load the page,
            # so we only do it if the geocoordinates are missing
            # This should have been done when the PDU was created
            paediatric_diabetes_unit_lead_organisation = fetch_organisation_by_ods_code(
                ods_code=paediatric_diabetes_unit.lead_organisation_ods_code
            )
            paediatric_diabetes_unit.lead_organisation_geocoordinates = Point(
                paediatric_diabetes_unit_lead_organisation["longitude"],
                paediatric_diabetes_unit_lead_organisation["latitude"],
                srid=4326,
            )
            paediatric_diabetes_unit.save()
        filtered_patients = Q(
            submissions__submission_active=True,
            submissions__audit_year=self.request.session.get("selected_audit_year"),
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

        # filter patients to the view preference of the user
        if not self.request.user.viewing_data_nationally():
            # PDU view
            filtered_patients &= Q(
                submissions__paediatric_diabetes_unit__pz_code=pz_code,
                submissions__paediatric_diabetes_unit__active=True
            )

        patient_queryset = patient_queryset.filter(filtered_patients)

        a_year_ago = timezone.now() - timezone.timedelta(days=365)

        this_audit_year_visits = visit_falls_within_audit_period_Q_object(
            audit_start_date=date(
                year=int(self.request.session.get("selected_audit_year")),
                month=4,
                day=1,
            ),
            prepend_query_path="visit",
        )

        patient_queryset = patient_queryset.annotate(
            audit_year=F("submissions__audit_year"),
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
                paediatric_diabetes_unit.lead_organisation_geocoordinates,
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

        pz_code = self.request.session.get("pz_code")
        selected_audit_year = self.request.session.get(
            "selected_audit_year"
        )  # this is the year that that audit period starts in

        pdu = PaediatricDiabetesUnit.objects.get(pz_code=pz_code) if pz_code else None
        context["pdu"] = pdu

        submission = None
        submission_error_count = 0

        # TODO MRB: this should probably be a method on the Submission model?
        #           https://github.com/rcpch/national-paediatric-diabetes-audit/issues/533
        if pz_code and selected_audit_year:
            submission = (
                Submission.objects.filter(
                    paediatric_diabetes_unit__pz_code=pz_code,
                    paediatric_diabetes_unit__active=True,
                    audit_year=selected_audit_year,
                )
                .order_by("-submission_date")
                .first()
            )

            if submission and submission.errors:
                submission_errors = json.loads(submission.errors)

                error_count = 0
                for errors_for_visit in submission_errors.values():
                    for errors_for_field in errors_for_visit.values():
                        submission_error_count += len(errors_for_field)

        context["submission"] = submission
        context["submission_valid_count"] = (
            context["paginator"].count - submission_error_count
        )
        context["submission_error_count"] = submission_error_count

        context["pz_code"] = pz_code
        context["selected_audit_year"] = selected_audit_year or "None"
        context["pdu_choices"] = (
            organisations_adapter.paediatric_diabetes_units_to_populate_select_field(
                requesting_user=self.request.user,
                user_instance=self.request.user,
            )
        )
        context["chosen_pdu"] = pz_code
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
    success_url = reverse_lazy("patients")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")
        AuditPeriod = apps.get_model("npda", "AuditPeriod")
        pz_code = self.request.session.get("pz_code")
        pdu = PaediatricDiabetesUnit.objects.get(pz_code=pz_code)
        audit_year = self.request.session.get("selected_audit_year")
        kwargs["paediatric_diabetes_unit"] = pdu
        kwargs["audit_period"] = AuditPeriod.objects.get_audit_period_for_request(self.request)
        kwargs["audit_year"] = audit_year
        # Get override_postcode from POST data if available
        if self.request.method in ('POST', 'PUT'):
            kwargs['override_postcode'] = self.request.POST.get('override_postcode', 'false') == 'true'
        return kwargs

    def get_context_data(self, **kwargs):
        PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")
        pz_code = self.request.session.get("pz_code")
        pdu = PaediatricDiabetesUnit.objects.get(pz_code=pz_code)
        context = super().get_context_data(**kwargs)
        title = f"Add New Child to {pdu.parent_name}  ({pdu.pz_code})"
        if (
            pdu.parent_name is not None
        ):  # if the PDU has a parent, include the parent name in the title
            title = f"Add New Child to  {pdu.parent_name} ({pz_code})"
        context["title"] = title
        context["button_title"] = "Create New Child Patient Record"
        context["form_method"] = "create"
        context["override_postcode"] = False
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
        if self.request.session.get("can_complete_questionnaire"):
            # the Patient record is therefore valid
            patient = form.save(commit=False)
            patient.is_valid = True
            patient.errors = None
            patient.save()

            # add the PDU to the patient record
            # get or create the paediatric diabetes unit object
            PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")
            paediatric_diabetes_unit = PaediatricDiabetesUnit.objects.get(
                pz_code=self.request.session.get("pz_code"),
            )

            Transfer = apps.get_model("npda", "Transfer")
            if Transfer.objects.filter(patient=patient).exists():
                # the patient is being transferred from another PDU. Update the previous_pz_code field
                transfer = Transfer.objects.get(patient=patient)
                transfer.previous_pz_code = transfer.paediatric_diabetes_unit.pz_code
                transfer.paediatric_diabetes_unit = paediatric_diabetes_unit
                transfer.date_leaving_service = (
                    form.cleaned_data.get("date_leaving_service"),
                )
                transfer.reason_leaving_service = (
                    form.cleaned_data.get("reason_leaving_service"),
                )
                transfer.save()
            else:
                Transfer.objects.create(
                    paediatric_diabetes_unit=paediatric_diabetes_unit,
                    patient=patient,
                    date_leaving_service=None,
                    reason_leaving_service=None,
                )
            # add patient to the latest audit year and the logged in user's PDU
            # the form is initialised with the current audit year

            Submission = apps.get_model("npda", "Submission")
            audit_period = AuditPeriod.objects.get_audit_period_for_request(self.request)

            submission, created = Submission.objects.update_or_create(
                audit_year=audit_period.audit_year(),
                paediatric_diabetes_unit=paediatric_diabetes_unit,
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
            # update the session - this stores that the user has used the questionnaire and disables csv upload
            refresh_session_filters(self.request, questionnaire=True)

        else:
            logger.error(
                f"User {self.request.user} attempted to add a new patient to the audit, but the submission for {self.request.session['pz_code']} is done through csv upload."
            )
            messages.error(
                self.request,
                "The submission for this PDU is done through csv upload and data cannot be added or edited through the questionnaire. If you need to edit the submission directly please contact the NPDA team for assistance.",
            )

        return super().form_valid(form)


class PatientUpdateView(
    LoginAndOTPRequiredMixin,
    CheckPDUInstanceMixin,
    PermissionRequiredMixin,
    SuccessMessageMixin,
    CheckCurrentAuditYearMixin,
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
    success_url = reverse_lazy("patients")
    Submission = apps.get_model("npda", "Submission")
    PatientSubmission = apps.get_model("npda", "PatientSubmission")

    def get_context_data(self, **kwargs):
        Transfer = apps.get_model("npda", "Transfer")
        # pz_code = self.request.session.get("pz_code")
        patient = Patient.objects.get(pk=self.kwargs["pk"])
        transfer = Transfer.objects.get(patient=patient)
        context = super().get_context_data(**kwargs)
        PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")
        pdu = PaediatricDiabetesUnit.objects.get(
            pz_code=transfer.paediatric_diabetes_unit.pz_code
        )
        title = f"Edit Child Details in {pdu.parent_name}  ({transfer.paediatric_diabetes_unit.pz_code})"
        if (
            transfer.paediatric_diabetes_unit.parent_name is not None
        ):  # if the PDU has a parent, include the parent name in the title
            title = f"Add New Child to {transfer.paediatric_diabetes_unit.parent_name} ({transfer.paediatric_diabetes_unit.pz_code})"
        context["title"] = title
        context["button_title"] = "Save Changes"
        context["form_method"] = "update"
        context["patient_id"] = self.kwargs["pk"]
        context["override_postcode"] = False
        return context

    def form_valid(self, form: BaseForm) -> HttpResponse:
        if "delete" in self.request.POST:
            return redirect(reverse("patient-delete", kwargs={"pk": self.kwargs["pk"]}))
        patient = form.save(commit=False)
        patient.is_valid = True
        patient.errors = None
        # TODO MRB: this calls patient.save twice. super.form_valid calls it too (https://github.com/rcpch/national-paediatric-diabetes-audit/issues/335)
        patient.save()
        return super().form_valid(form)
    
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
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Get override_postcode from POST data if available
        kwargs["audit_period"] = AuditPeriod.objects.get_audit_period_for_request(self.request)
        if self.request.method in ('POST', 'PUT'):
            kwargs['override_postcode'] = self.request.POST.get('override_postcode', 'false') == 'true'
        return kwargs
    


class PatientDeleteView(
    LoginAndOTPRequiredMixin,
    CheckPDUInstanceMixin,
    PermissionRequiredMixin,
    SuccessMessageMixin,
    CheckCurrentAuditYearMixin,
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

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            return redirect(reverse("patient-update", kwargs={"pk": self.kwargs["pk"]}))
        return super().post(request, *args, **kwargs)
