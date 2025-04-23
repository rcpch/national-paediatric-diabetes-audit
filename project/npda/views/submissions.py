# Python imports
from datetime import date
import json
from typing import Any, Iterable

# Django imports
from django.apps import apps
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Case, When, F, Value, IntegerField, OuterRef, Subquery
from django.db.models.functions import Concat, ExtractMonth, ExtractYear
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import ListView

# Third party imports
import pandas as pd
import plotly.graph_objects as go

from project.npda.views.decorators import login_and_otp_required

# RCPCH imports
from project.constants.colors import RCPCH_LIGHT_BLUE
from ..general_functions.session import refresh_session_filters
from ..general_functions.csv import (
    download_csv,
    download_xlsx,
)
from .mixins import LoginAndOTPRequiredMixin
from ..models import (
    Submission,
    OrganisationEmployer,
    PaediatricDiabetesUnit,
    AuditPeriod,
    Patient
)


class SubmissionsListView(
    LoginAndOTPRequiredMixin, ListView
):
    """
    The SubmissionsListView class.

    This class is used to display a list of submissions.

    Users with permisson should be able to view all submissions for the PDU & ODS code in the session for all audit years/quarters.
    Only one submission per audit year/quarter should be active.
    It is only possible to create/update/delete a submission for the current audit year/quarter.
    """

    model = apps.get_model(app_label="npda", model_name="Submission")
    template_name = "submissions_list.html"
    context_object_name = "submissions"

    def get_queryset(self) -> Iterable[Any]:
        """
        Retrieve all submissions for the current PZ code, unless view_preference is set to 2 (national view)
        """
        PaediatricDiabetesUnit = apps.get_model(
            app_label="npda", model_name="PaediatricDiabetesUnit"
        )
        pdu = PaediatricDiabetesUnit.objects.get(
            pz_code=self.request.session.get("pz_code"),
        )
        if self.request.user.viewing_data_nationally():
            base_queryset = self.model.objects.filter(
                audit_year=self.request.session.get("selected_audit_year")
            ).all()
        else:
            base_queryset = self.model.objects.filter(
                paediatric_diabetes_unit=pdu,
                audit_year=self.request.session.get("selected_audit_year"),
            )

        final = base_queryset.annotate(
            patient_count=Count("patients"),
            full_name_submission_by=Concat(
                "submission_by__first_name", Value(" "), "submission_by__surname"
            ),
        ).order_by(
            "audit_year",
            "-submission_active",
            "-submission_date",
        )

        return final

    def get_context_data(self, **kwargs: Any) -> dict:
        """
        Add data to the context.
        Includes the patient data for the active submission and the csv summary data.
        """
        if self.request.session.get("pz_code") == "PZ248":
            is_jersey = True
        else:
            is_jersey = False
        context = super().get_context_data(**kwargs)
        context["pz_code"] = self.request.session.get("pz_code")
        context["selected_audit_year"] = self.request.session.get("selected_audit_year")
        Patient = apps.get_model("npda", "Patient")
        context["data"] = None  # data stores csv summary data if a submission exists
        context["column_chart"] = None
        context["submission_statistics"] = None
        requested_active_submission = self.object_list.filter(
            submission_active=True,
            audit_year=self.request.session.get("selected_audit_year"),
            paediatric_diabetes_unit__pz_code=self.request.session.get("pz_code"),
            paediatric_diabetes_unit__active=True,
        ).first()  # there can be only one of these
        if requested_active_submission:
            if requested_active_submission.errors:
                deserialized_errors = json.loads(requested_active_submission.errors)
                context["submission_errors"] = deserialized_errors
            else:
                context["submission_errors"] = None
            # Get some summary data about the patients in the submission...
            context["patients"] = Patient.objects.filter(
                submissions=requested_active_submission
            ).annotate(
                visit_error_count=Count(Case(When(visit__is_valid=False, then=1))),
                visit_count=Count("visit"),
            )
        
        if self.request.user.viewing_data_nationally():
            selected_audit_year = self.request.session.get("selected_audit_year")

            latest_active_submission = Submission.objects.filter(
                paediatric_diabetes_unit=OuterRef("pk"),
                submission_active=True,
                audit_year=selected_audit_year,
            ).order_by("paediatric_diabetes_unit").values("submission_date")[:1]

            paediatric_diabetes_units = PaediatricDiabetesUnit.objects.annotate(
                latest_submission_date=Subquery(latest_active_submission),
                submission_month=ExtractMonth("latest_submission_date"),
                submission_year_raw=ExtractYear("latest_submission_date"),
                # Determine the audit year for the submission date
                audit_year_for_submission=Case(
                    When(submission_month__gte=4, then=F("submission_year_raw")),
                    default=F("submission_year_raw") - 1,
                    output_field=IntegerField(),
                ),
                # Define the start dates for each quarter based on the audit year (using the selected audit year for context)
                quarter1_start=Case(
                    When(submission_month__gte=4, then=date(selected_audit_year, 4, 1)),
                    default=date(selected_audit_year - 1, 4, 1),
                ),
                quarter2_start=Case(
                    When(submission_month__gte=4, then=date(selected_audit_year, 7, 1)),
                    default=date(selected_audit_year - 1, 7, 1),
                ),
                quarter3_start=Case(
                    When(submission_month__gte=4, then=date(selected_audit_year, 10, 1)),
                    default=date(selected_audit_year - 1, 10, 1),
                ),
                quarter4_start=Case(
                    When(submission_month__gte=4, then=date(selected_audit_year + 1, 1, 1)),
                    default=date(selected_audit_year, 1, 1),
                ),
                quarter4_end=Case(
                    When(submission_month__gte=4, then=date(selected_audit_year + 1, 3, 31)),
                    default=date(selected_audit_year, 3, 31),
                ),
                # Determine the quarter using conditional expressions
                latest_submission_quarter=Case(
                    When(latest_submission_date__gte=F("quarter1_start"), latest_submission_date__lt=F("quarter2_start"), then=Value(1)),
                    When(latest_submission_date__gte=F("quarter2_start"), latest_submission_date__lt=F("quarter3_start"), then=Value(2)),
                    When(latest_submission_date__gte=F("quarter3_start"), latest_submission_date__lt=F("quarter4_start"), then=Value(3)),
                    When(latest_submission_date__gte=F("quarter4_start"), latest_submission_date__lte=F("quarter4_end"), then=Value(4)),
                    output_field=IntegerField(),
                ),
            ).values("pz_code", "lead_organisation_name", "latest_submission_quarter")
            column_chart = create_column_chart(paediatric_diabetes_units, selected_audit_year)
            context["column_chart"] = column_chart.to_html(full_html=False)
            context["submission_statistics"] = submission_stats(selected_audit_year)

        return context

    def get(self, request, *args, **kwargs):
        """
        Handle the HTMX GET request to filter submissions based on the 'done' parameter.
        """
        queryset = self.get_queryset().order_by("-submission_date")
        self.object_list = queryset
        context = self.get_context_data(object_list=self.object_list)
        
        template = self.template_name

        if request.htmx:
            template = "partials/submission_history.html"

        return render(request=request, template_name=template, context=context)

    def post(self, request, *args, **kwargs):
        """
        Handle the HTMX POST request.
        The button name "submit-data" is used to determine the action to be taken.
        If the value of "submit-data" is "delete-data", the submission is deleted.
        If the value of "submit-data" is "download-data", the original csv is downloaded.
        If the value of "submit-data" is "download-report", the commented xlsx (with validation remarks) is downloaded.
        """
        if request.htmx:
            # HTMX request
            template = "partials/submission_history.html"
            queryset = self.get_queryset().order_by("-submission_date")
            toggle_result = request.POST.get('toggle_inactive_submissions', "off")

            # If toggle is OFF (not submitted/unchecked), only show active submissions
            # If toggle is ON (checked), show all submissions
            if toggle_result != 'on':
                toggle_result = "off"
            else:
                toggle_result = "on"  # Keep it "on" if it was sent as "on"
                queryset = queryset.filter(submission_active=True)

            self.object_list = queryset
            print(f"Toggle result after: {toggle_result}")
            context = self.get_context_data(object_list=self.object_list)
            context["toggle_inactive_submissions"] = toggle_result
            return render(request=request, template_name=template, context=context)

        
        button_name = request.POST.get("submit-data")
        if button_name == "delete-data":
            # check if the user has permission to delete submissions
            if not request.user.has_perm("npda.delete_submission"):
                raise PermissionDenied(
                    "You do not have permission to delete submissions.",
                )
            # retrieve the  submission instance
            submission = Submission.objects.filter(
                pk=request.POST.get("audit_id")
            ).get()

            # check if the submission is active - if so, do not allow deletion, and return an error message
            if submission.submission_active:
                self.object_list = self.get_queryset()
                context = self.get_context_data(object_list=self.object_list)
                messages.error(
                    request,
                    "Cannot delete an active submission. Please make another submission active before deleting this one",
                )
                return render(request, self.template_name, context=context)

            # delete the patients associated with the submission
            submission.patients.all().delete()
            # then delete the submission itself
            submission.delete()

            # set the submission_active flag to True for the most recent submission
            if Submission.objects.count() > 0:
                new_first = Submission.objects.order_by("-submission_date").first()
                new_first.submission_active = True
                new_first.save()
            messages.success(request, "Cohort submission deleted successfully")

        if button_name == "download-data":
            # check if the user has permission to download submissions
            if not request.user.has_perm("npda.can_download_csv"):
                raise PermissionDenied(
                    "You do not have permission to download CSVs.",
                )
            submission = Submission.objects.filter(
                pk=request.POST.get("audit_id")
            ).get()
            return download_csv(request, submission.id)

        if button_name == "download-report":
            # check if the user has permission to download submissions
            if not request.user.has_perm("npda.can_download_csv"):
                raise PermissionDenied(
                    "You do not have permission to download submissions.",
                )
            submission = Submission.objects.filter(
                pk=request.POST.get("audit_id")
            ).get()
            return download_xlsx(request, submission.id)

        # POST is not supported for this view
        # Must therefore return the queryset as an obect_list and context
        self.object_list = self.get_queryset()
        context = self.get_context_data(object_list=self.object_list)
        return render(request, self.template_name, context=context)

    def render_to_response(self, context: dict) -> HttpResponse:
        """
        Render the response.

        :param context: The context
        :return: The response
        """
        return super().render_to_response(context)


@login_and_otp_required()
def upload_csv(request):
    context = {"employers": OrganisationEmployer.objects.filter(npda_user=request.user)}
    return render(request, "upload_csv/file_upload.html", context=context)

@login_and_otp_required()
def upload_csv_in_progress(request):
    pz_code = request.session.get("pz_code")
    audit_period = AuditPeriod.objects.get_audit_period_for_request(request)

    last_submission = Submission.objects.filter(
        paediatric_diabetes_unit__pz_code=pz_code,
        audit_year=audit_period.audit_year(),
    ).order_by("-submission_date").first()

    if last_submission and not last_submission.submission_active:
        patients_so_far = Patient.objects.filter(submissions=last_submission).count()
        visits_so_far = Patient.objects.filter(submissions=last_submission).aggregate(Count("visit"))["visit__count"]

        context = {
            "csv_file_name": last_submission.csv_file_name,
            "patients_so_far": patients_so_far,
            "visits_so_far": visits_so_far
        }

        return render(request, "upload_csv/upload_in_progress.html", context=context)
    
    return redirect("patients") 

@login_and_otp_required()
def switch_paediatric_diabetes_unit(request):
    """
    Switch the Paediatric Diabetes Unit in the session.
    This is an HTMX view.
    """
    template = "partials/submission_employer_selector.html"
    error_message = None

    selected_pz_code = request.POST.get("employers")
    if selected_pz_code == request.session.get("pz_code"):
        return HttpResponse(status=200)

    try:
        pdu = PaediatricDiabetesUnit.objects.get(pz_code=selected_pz_code)
    except PaediatricDiabetesUnit.DoesNotExist as error:
        error_message = f"Error: {error}. Please contact the NPDA team."

    context = {
        "employers": OrganisationEmployer.objects.filter(npda_user=request.user),
        "error_message": error_message,
    }
    # update the session with the new PDU
    refresh_session_filters(request, pz_code=selected_pz_code)

    return render(request, template, context=context)

def create_column_chart(pdus_by_latest_submission, selected_audit_year):
    """
    Create a column chart based on the latest submission data.
    """
    # Create a Pandas DataFrame
    df = pd.DataFrame(pdus_by_latest_submission)

    # Create the Plotly column chart
    fig = go.Figure(data=[go.Bar(x=df['pz_code'], y=df['latest_submission_quarter'], marker_color=RCPCH_LIGHT_BLUE)])

    # Update layout
    fig.update_layout(
        title=f"Latest Submission Quarter by PZ Code (Audit Year: {selected_audit_year})",
        xaxis_title="PZ Code",
        yaxis_title="Latest Submission Quarter",
        xaxis=dict(
            tickangle=-45,
            tickfont=dict(color='black')  # Set a default color for all labels
        ),
        yaxis=dict(
            tickvals=[1, 2, 3, 4],
            ticktext=["Q1", "Q2", "Q3", "Q4"]
        ),
        paper_bgcolor='white',
        
    )

    return fig

def submission_stats(selected_audit_year):
    """
    View to display submission statistics.
    - the paediatric diabetes unit with the most recent submission
    - the paediatric diabetes unit with the least errors
    - the paediatric diabetes unit with the most patients
    - the paediatric diabetes unit with the most visits
    """

    # Retrieve the latest submission data for the selected audit year
    latest_submission_data = Submission.objects.filter(
        audit_year=selected_audit_year,
        submission_date__gte=date.today(),
        paediatric_diabetes_unit__active=True,
        submission_active=True
    ).order_by(
        '-submission_date'
    ).first()

    fewest_errors = Submission.objects.filter(
        audit_year = selected_audit_year,
        submission_active=True,
        paediatric_diabetes_unit__active=True
    ).annotate(
        error_count=Count('errors')
    ).order_by(
        'error_count'
    ).first()

    most_patients = Submission.objects.filter(
        audit_year = selected_audit_year,
        submission_active=True,
        paediatric_diabetes_unit__active=True
    ).annotate(
        patient_count=Count('patients')
    ).order_by(
        '-patient_count'
    ).first()

    most_visits = Submission.objects.filter(
        audit_year = selected_audit_year,
        submission_active=True,
        paediatric_diabetes_unit__active=True
    ).annotate(
        visit_count=Count('patients__visit'),
        visits_per_patient=Count('patients')/Count('patients__visit')
    ).order_by(
        '-visits_per_patient'
    ).first()

    latest_submission_paediatric_diabetes_unit, submission_date = getattr(latest_submission_data, "paediatric_diabetes_unit", None), getattr(latest_submission_data,"submission_date", None)
    fewest_errors_paediatric_diabetes_unit, error_number = getattr(fewest_errors, "paediatric_diabetes_unit", None), getattr(fewest_errors,"error_count", None)
    most_patients_paediatric_diabetes_unit, patient_number = getattr(most_patients, "paediatric_diabetes_unit", None), getattr(most_patients,"patient_count", None)
    most_visits_paediatric_diabetes_unit, visit_number = getattr(most_visits, "paediatric_diabetes_unit", None), getattr(most_visits,"visits_per_patient", None)

    # Create a dictionary to store the statistics
    submission_statistics = {
        "latest_submission": {
            "pdu": latest_submission_paediatric_diabetes_unit,
            "submission_date": submission_date,
        },
        "fewest_errors": {
            "pdu": fewest_errors_paediatric_diabetes_unit,
            "error_number": error_number,
        },
        "most_patients": {
            "pdu": most_patients_paediatric_diabetes_unit,
            "patient_number": patient_number,
        },
        "most_visits": {
            "pdu": most_visits_paediatric_diabetes_unit,
            "visit_number_per_patient": visit_number,
        },
    }
    return submission_statistics


    