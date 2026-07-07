# Python imports
import io
import itertools
import json
import logging
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

# Third party imports
import pandas as pd
import plotly.graph_objects as go

# Django imports
from django.apps import apps
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import (
    Case,
    Count,
    Exists,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Concat, ExtractMonth, ExtractYear
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import ListView

# RCPCH imports
from project.constants.colors import RCPCH_LIGHT_BLUE
from project.npda.views.decorators import check_data_permissions, login_and_otp_required
from project.settings import RCPCH_CENSUS_PLATFORM_TOKEN, RCPCH_DEPRIVATION_TILES_URL

from ..general_functions.breadcrumbs import data_breadcrumbs
from ..general_functions.csv import (
    create_csv_submission,
    csv_parse,
    download_csv_file,
    download_xlsx,
    export_as_csv,
)
from ..general_functions.patient_report.queries import (
    all_pdus_age_map_data,
    all_pdus_care_processes_map_data,
    all_pdus_diabetes_type_map_data,
    all_pdus_t1dm_bubble_map_data,
)
from ..general_functions.session import save_csv_uploading_user_to_visitactivity
from ..models import (
    PaediatricDiabetesUnit,
    Patient,
    PatientSubmission,
    Submission,
    Transfer,
)
from ..signals import get_client_ip
from ..tasks import upload_csv_task
from .mixins import LoginAndOTPRequiredMixin, PDUPermissionMixin

logger = logging.getLogger(__name__)


class SubmissionsListView(
    LoginAndOTPRequiredMixin, PDUPermissionMixin, PermissionRequiredMixin, ListView
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
    permission_required = "npda.view_submission"
    permission_denied_message = "You do not have permission to view submissions."

    def get_queryset(self) -> Iterable[Any]:
        base_args = {
            "audit_period": self.audit_period,
            "paediatric_diabetes_unit": self.pdu,
        }

        if self.request.user.is_rcpch_audit_team_member:
            del base_args["paediatric_diabetes_unit"]
            # Don't show inactive submissions to admins, it makes the page very heavy
            base_args["submission_active"] = True

        base_queryset = self.model.objects.filter(**base_args)

        # Avoid N+1 query problem, especially painful on national view
        final = base_queryset.select_related(
            "paediatric_diabetes_unit",
            "submission_by",
        )

        final = final.annotate(
            patient_count=Count("patients"),
            full_name_submission_by=Concat(
                "submission_by__first_name", Value(" "), "submission_by__surname"
            ),
            latest_patient_visit_date=Subquery(
                Patient.objects.filter(
                    submissions=OuterRef("pk"), visit__visit_date__isnull=False
                )
                .order_by("-visit__visit_date")
                .values("visit__visit_date")[:1]
            ),
        ).order_by(
            "audit_year",
            "-submission_active",
            "-submission_date",
            "-latest_patient_visit_date",
        )

        return final

    def get_context_data(self, **kwargs: Any) -> dict:
        """
        Add data to the context.
        Includes the patient data for the active submission and the csv summary data.
        """
        context = super().get_context_data(**kwargs)
        Patient = apps.get_model("npda", "Patient")
        context["data"] = None  # data stores csv summary data if a submission exists
        context["column_chart"] = None
        context["submission_statistics"] = None
        requested_active_submission = self.object_list.filter(
            submission_active=True,
            audit_period=self.audit_period,
            paediatric_diabetes_unit=self.pdu,
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

        if self.request.user.is_rcpch_audit_team_member:
            selected_audit_period = self.audit_period
            # Start with ALL active PDUs, not just those with submissions
            chart_data = (
                PaediatricDiabetesUnit.objects.filter(active=True)
                .annotate(
                    # Get the latest visit date from active submissions (if any)
                    latest_patient_visit_date=Subquery(
                        self.get_queryset()
                        .filter(
                            paediatric_diabetes_unit=OuterRef("pk"),
                            submission_active=True,
                            latest_patient_visit_date__isnull=False,
                        )
                        .values("latest_patient_visit_date")[:1]
                    ),
                    # Extract month and year from the latest visit date
                    visit_month=ExtractMonth("latest_patient_visit_date"),
                    visit_year_raw=ExtractYear("latest_patient_visit_date"),
                    # Calculate quarter based on visit date (None for PDUs with no submissions)
                    latest_visit_quarter=Case(
                        When(visit_month__in=[4, 5, 6], then=Value(1)),
                        When(visit_month__in=[7, 8, 9], then=Value(2)),
                        When(visit_month__in=[10, 11, 12], then=Value(3)),
                        When(visit_month__in=[1, 2, 3], then=Value(4)),
                        default=Value(0),  # 0 for PDUs with no submissions
                        output_field=IntegerField(),
                    ),
                )
                .values("pz_code", "lead_organisation_name", "latest_visit_quarter")
            )

            context["pdu_submission_data"] = list(
                chart_data.order_by("latest_visit_quarter", "pz_code").values(
                    "pz_code", "lead_organisation_name", "latest_visit_quarter"
                )
            )
            context["non_submission_pdus"] = chart_data.filter(
                latest_visit_quarter=0
            ).values_list("pz_code", "lead_organisation_name")
            context["audit_period"] = selected_audit_period
            context["submission_statistics"] = submission_stats(selected_audit_period)
            context["bubble_map_centres"] = all_pdus_t1dm_bubble_map_data(
                selected_audit_period
            )
            context["bubble_map_care_processes"] = all_pdus_care_processes_map_data(
                selected_audit_period
            )
            context["bubble_map_diabetes_type"] = all_pdus_diabetes_type_map_data(
                selected_audit_period
            )
            context["bubble_map_age"] = all_pdus_age_map_data(selected_audit_period)
            context["RCPCH_DEPRIVATION_TILES_URL"] = RCPCH_DEPRIVATION_TILES_URL
            context["RCPCH_CENSUS_PLATFORM_TOKEN"] = RCPCH_CENSUS_PLATFORM_TOKEN

        context["breadcrumbs"] = data_breadcrumbs(
            self.pdu,
            self.audit_period,
            [
                ("Patient Data", "pdu-patients"),
                ("Submissions", "pdu-submissions"),
            ],
        )

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
            toggle_result = request.POST.get("toggle_inactive_submissions", "off")

            # If toggle is OFF (not submitted/unchecked), only show active submissions
            # If toggle is ON (checked), show all submissions
            if toggle_result != "on":
                toggle_result = "off"
            else:
                toggle_result = "on"  # Keep it "on" if it was sent as "on"
                queryset = queryset.filter(submission_active=True)

            self.object_list = queryset
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
            if (
                request.user.is_rcpch_audit_team_member
                or submission.paediatric_diabetes_unit
                in request.user.organisation_employers.all()
            ):
                if submission.csv_file_name:
                    return download_csv_file(request, submission.id)
                else:
                    return export_as_csv(request, submission)
            else:
                raise PermissionDenied(
                    f"User {request.user.email} does not have permission to download data for PDU {submission.paediatric_diabetes_unit.pz_code}.",
                )

        if button_name == "download-report":
            # check if the user has permission to download submissions
            if not request.user.has_perm("npda.can_download_csv"):
                raise PermissionDenied(
                    "You do not have permission to download submissions.",
                )
            submission = Submission.objects.filter(
                pk=request.POST.get("audit_id")
            ).get()
            if (
                request.user.is_rcpch_audit_team_member
                or submission.paediatric_diabetes_unit
                in request.user.organisation_employers.all()
            ):
                return download_xlsx(request, submission.id)
            else:
                raise PermissionDenied(
                    f"User {request.user.email} does not have permission to download data for PDU {submission.paediatric_diabetes_unit.pz_code}.",
                )

        if button_name == "start-questionnaire-submission":
            previous_audit_period = self.audit_period.previous_audit_period()

            next_submission = Submission.objects.get_submission_for_request(
                self.pdu, self.audit_period
            )
            last_submission = Submission.objects.get_submission_for_request(
                self.pdu, previous_audit_period
            )

            if next_submission:
                raise RuntimeError(
                    f"Cannot start questionnaire submission. Active submission already exists for this audit period. audit_period={self.audit_period}, previous_audit_period={previous_audit_period}, pdu={self.pdu.pz_code}"
                )

            last_patients = (
                last_submission.patients.all()
                if last_submission
                else Patient.objects.none()
            )

            last_patients = last_patients.exclude(death_date__isnull=False).exclude(
                Exists(
                    Transfer.objects.filter(
                        Q(patient=OuterRef("pk"))
                        & Q(reason_leaving_service__isnull=False)
                    )
                )
            )

            # Clone
            for patient in last_patients:
                patient.pk = None

            with transaction.atomic():
                next_submission = Submission.objects.create(
                    paediatric_diabetes_unit=self.pdu,
                    audit_period=self.audit_period,
                    audit_year=self.audit_period.audit_year(),
                    submission_active=True,
                    submission_by=request.user,
                    submission_date=datetime.now(UTC),
                )

                next_patients = Patient.objects.bulk_create(last_patients)

                next_patient_transfers = [
                    Transfer(patient=patient, paediatric_diabetes_unit=self.pdu)
                    for patient in next_patients
                ]
                Transfer.objects.bulk_create(next_patient_transfers)

                next_patient_subs = [
                    PatientSubmission(patient=patient, submission=next_submission)
                    for patient in next_patients
                ]
                PatientSubmission.objects.bulk_create(next_patient_subs)

            return redirect(
                "pdu-patients",
                pz_code=self.pdu.pz_code,
                audit_period=self.audit_period.slug,
            )

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
@check_data_permissions()
def upload_csv(request, audit_period, pdu):
    def upload_error(message):
        logger.error(
            "CSV upload failed. pz_code=%s audit_period=%s error_message=%s",
            pdu.pz_code,
            audit_period.slug,
            message,
        )

        messages.error(
            request=request,
            message=message,
        )
        return redirect(
            "pdu-upload-csv", pz_code=pdu.pz_code, audit_period=audit_period.slug
        )

    previous_submission = Submission.objects.get_submission_for_request(
        pdu, audit_period
    )

    if previous_submission and not previous_submission.csv_file_name:
        # PDU is submitting via questionnaire
        return redirect(
            reverse(
                "pdu-dashboard",
                kwargs={
                    "audit_period": audit_period.slug,
                    "pz_code": pdu.pz_code,
                },
            )
        )

    if request.method == "POST":
        has_perm = request.user.has_perm("npda.can_submit_csv")
        if not has_perm:
            raise PermissionDenied("You do not have permission to upload CSV files.")

        user_csv = request.FILES["csv_upload"]
        user_csv_filename = user_csv.name
        # We are eventually storing the CSV file as a BinaryField so have to hold it in memory
        user_csv_bytes = user_csv.read()

        pz_code = pdu.pz_code
        is_jersey = pz_code == "PZ248"
        dataset_year = audit_period.get_dataset_year()

        # check to see if the CSV is valid - cannot accept CSVs with no header. All other header errors are non-lethal but are reported back to the user
        try:
            parsed_csv = csv_parse(
                io.BytesIO(user_csv_bytes), dataset_year=dataset_year
            )
        except ValueError as e:
            return upload_error(f"Invalid CSV format: {e}")

        missing_columns = parsed_csv.missing_columns
        if not parsed_csv.identifier_column:
            missing_columns.append(
                "Unique Reference Number" if is_jersey else "NHS Number"
            )

        if (
            missing_columns
            or parsed_csv.additional_columns
            or parsed_csv.duplicate_columns
        ):
            logger.error(
                "CSV upload failed due to column issues. pz_code=%s missing_columns=%s additional_columns=%s duplicate_columns=%s",
                pz_code,
                missing_columns,
                parsed_csv.additional_columns,
                parsed_csv.duplicate_columns,
            )

            return render(
                request,
                "upload_csv/file_upload.html",
                context={
                    "csv_and_template_columns": list(
                        itertools.zip_longest(
                            parsed_csv.template_columns, parsed_csv.df.columns
                        )
                    ),
                    "missing_columns": parsed_csv.missing_columns,
                    "additional_columns": parsed_csv.additional_columns,
                    "duplicate_columns": parsed_csv.duplicate_columns,
                },
            )

        if parsed_csv.identifier_column == "Unique Reference Number" and not is_jersey:
            return upload_error(
                "CSV file must use NHS number as the identifier column unless uploading for Jersey"
            )

        #  the same must be true for the Jersey upload
        if parsed_csv.identifier_column == "NHS Number" and is_jersey:
            return upload_error(
                "CSV file must use Unique Reference Number as the identifier column unless uploading for Jersey"
            )

        # https://github.com/rcpch/national-paediatric-diabetes-audit/issues/1344
        # Gracefully handle missing values in the "PDU Number" column
        unique_pdu_numbers = parsed_csv.df["PDU Number"].dropna().unique()

        if len(unique_pdu_numbers) > 1:
            message = f"CSV file contains multiple PDU Numbers: {', '.join(unique_pdu_numbers)}. Please upload a file containing data for a single PDU only."
            return upload_error(message)

        # 1316 - Twinkle/Diamond outputs PDU number without leading PZ and zeros
        expected_pdu_number = pdu.pz_code[2:].lstrip("0")
        
        if len(unique_pdu_numbers) > 0:
            pdu_number_in_csv = unique_pdu_numbers[0]

            if pdu_number_in_csv.startswith("PZ"):
                pdu_number_in_csv = pdu_number_in_csv[2:]

            # 1464 - Twinkle outputs PDU number as a decimal (e.g. "180.0")
            if pdu_number_in_csv.endswith(".0"):
                pdu_number_in_csv = pdu_number_in_csv[:-2]
            
            pdu_number_in_csv = pdu_number_in_csv.lstrip("0")
        else:
            pdu_number_in_csv = None

        print(f"PDU number in CSV: {pdu_number_in_csv}, expected PDU number: {expected_pdu_number}")

        if pdu_number_in_csv != expected_pdu_number:
            message = f"PDU Number in CSV file ({unique_pdu_numbers[0]}) does not match the PDU you are looking at ({pdu.pz_code}). Please upload a file with the correct PDU Number."
            return upload_error(message)

        if not audit_period.is_open and not (
            request.user.is_superuser or request.user.is_rcpch_audit_team_member
        ):
            raise PermissionDenied(f"Upload is closed for {audit_period}.")

        new_submission = create_csv_submission(
            pdu=pdu,
            audit_period=audit_period,
            csv_file_bytes=user_csv_bytes,
            csv_file_name=user_csv_filename,
            # The celery task will flip it to active once complete
            submission_active=False,
            user=request.user,
            ip_address=get_client_ip(request),
            new_dataframe=parsed_csv.df,
        )

        upload_csv_task.delay(new_submission.id)

        save_csv_uploading_user_to_visitactivity(request=request)

        return redirect(
            "pdu-upload-csv-in-progress",
            pz_code=pdu.pz_code,
            audit_period=audit_period.slug,
        )

    return render(
        request,
        "upload_csv/file_upload.html",
        context={
            "pdu": pdu,
            "breadcrumbs": data_breadcrumbs(
                pdu,
                audit_period,
                [
                    ("Patient Data", "pdu-patients"),
                    ("Upload CSV", "pdu-upload-csv"),
                ],
            ),
        },
    )


@login_and_otp_required()
@check_data_permissions()
def upload_csv_in_progress(request, audit_period, pdu):
    last_submission = (
        Submission.objects.filter(
            paediatric_diabetes_unit=pdu, audit_period=audit_period
        )
        .order_by("-submission_date")
        .first()
    )

    seconds_since_submission = (
        datetime.now(UTC) - last_submission.submission_date
    ).seconds

    timeout = seconds_since_submission > 120

    total_patients = last_submission.total_unique_patients
    total_rows = last_submission.total_unique_visits
    patients_so_far = Patient.objects.filter(submissions=last_submission).count()
    visits_so_far = Patient.objects.filter(submissions=last_submission).aggregate(
        Count("visit")
    )["visit__count"]
    upload_complete = total_rows == visits_so_far and total_patients == patients_so_far
    csv_file_name = last_submission.csv_file_name
    if timeout:
        upload_complete = True  # if timeout, we assume the upload is complete as this triggers redirect to upload_complete template
        if not last_submission:
            # here there is an error with the headers or the csv file is empty
            # we return an error message to the user and redirect them to the patients page
            messages.error(
                request,
                "The upload has timed out. Please try again.",
            )
            return redirect("patients")

    context = {
        "csv_file_name": csv_file_name,
        "patients_so_far": patients_so_far,
        "visits_so_far": visits_so_far,
        "total_patients": total_patients,
        "total_rows": total_rows,
        "patient_progress": patients_so_far / total_patients * 100
        if total_patients
        else 0,
        "upload_complete": upload_complete,
        "timeout": timeout,
        "breadcrumbs": data_breadcrumbs(
            pdu,
            audit_period,
            [
                ("Patient Data", "pdu-patients"),
                ("Uploading CSV", "pdu-upload-csv-in-progress"),
            ],
        ),
    }

    if request.htmx:
        response = render(
            request, "upload_csv/upload_in_progress_wrapper.html", context=context
        )
        return response

    return render(request, "upload_csv/upload_in_progress.html", context=context)


def create_column_chart(pdus_by_latest_submission, selected_audit_period):
    """
    Create a bar chart based on the latest submission data.
    """
    # Create a Pandas DataFrame
    df = pd.DataFrame(pdus_by_latest_submission)

    # Create horizontal bar chart (quarters on x-axis, PDUs on y-axis)
    fig = go.Figure(
        data=[
            go.Bar(
                x=df["latest_visit_quarter"],  # Quarter values on x-axis
                y=df["pz_code"],  # PZ codes on y-axis (creates horizontal bars)
                customdata=df[
                    "lead_organisation_name"
                ],  # Use lead_organisation_name for hover text
                orientation="h",  # Horizontal orientation
                marker_color=RCPCH_LIGHT_BLUE,
                text=[
                    f"Q{q}" if q > 0 else "No Data" for q in df["latest_visit_quarter"]
                ],
                textposition="inside",  # Text inside bars for horizontal layout
                hovertemplate="<b>%{y} (%{customdata})</b><br>Quarter: %{text}<extra></extra>",
                textfont={
                    "color": "white",
                    "size": 12,
                    "family": "Montserrat",  # Change font family
                },
                hoverlabel={
                    "bgcolor": RCPCH_LIGHT_BLUE,
                    "bordercolor": RCPCH_LIGHT_BLUE,
                    "font": {"color": "white", "size": 14, "family": "Montserrat"},
                },
            )
        ]
    )

    # Update layout for horizontal bars
    fig.update_layout(
        title={
            "text": f"Latest Submission Data by Quarter (using latest visit date) against PZ Code (Audit Period: {selected_audit_period.slug})",
            "font": {"family": "Montserrat", "size": 16, "color": "black"},
            "x": 0.5,  # Center the title horizontally
            "xanchor": "center",  # Anchor the title at its center
        },
        xaxis_title="Latest Quarter (by Latest Visit Date)",
        yaxis_title="PZ Code",
        xaxis={
            "tickvals": [0, 1, 2, 3, 4],
            "ticktext": ["No Data", "Q1", "Q2", "Q3", "Q4"],
            "range": [0, 4.5],  # Ensure all values are visible
        },
        yaxis={
            "tickfont": {"color": "black", "size": 10},  # Smaller font for many PDUs
            "automargin": True,  # Auto-adjust margins for long PDU names
        },
        paper_bgcolor="white",
        height=max(400, len(df) * 25),  # Dynamic height based on number of PDUs
        margin={"l": 100, "r": 50, "t": 80, "b": 50},  # Adjust margins for PDU labels
        showlegend=False,
    )

    return fig


def submission_stats(selected_audit_period):
    """
    View to display submission statistics.
    - the paediatric diabetes unit with the most recent submission
    - the paediatric diabetes unit with the least errors
    - the paediatric diabetes unit with the most patients
    - the paediatric diabetes unit with the most visits
    """

    # Retrieve the latest submission data for the selected audit year
    latest_submission_data = Submission.objects.filter(
        audit_period=selected_audit_period,
        paediatric_diabetes_unit__active=True,
        submission_active=True,
    ).order_by("-submission_date")
    if latest_submission_data.exists():
        latest_submission_data = latest_submission_data.first()
    else:
        latest_submission_data = None

    fewest_errors = (
        Submission.objects.filter(
            audit_period=selected_audit_period,
            submission_active=True,
            paediatric_diabetes_unit__active=True,
        )
        .annotate(error_count=Count("errors"))
        .order_by("error_count")
    )
    if fewest_errors.exists():
        fewest_errors = fewest_errors.first()
    else:
        fewest_errors = None

    most_patients = (
        Submission.objects.filter(
            audit_period=selected_audit_period,
            submission_active=True,
            paediatric_diabetes_unit__active=True,
        )
        .annotate(patient_count=Count("patients"))
        .order_by("-patient_count")
    )
    if most_patients.exists():
        most_patients = most_patients.first()
    else:
        most_patients = None

    most_visits = (
        Submission.objects.filter(
            audit_period=selected_audit_period,
            submission_active=True,
            paediatric_diabetes_unit__active=True,
        )
        .annotate(
            visit_count=Count("patients__visit"),
            visits_per_patient=Count("patients") / Count("patients__visit"),
        )
        .order_by("-visits_per_patient")
    )

    latest_submission_paediatric_diabetes_unit, submission_date = (
        getattr(latest_submission_data, "paediatric_diabetes_unit", None),
        getattr(latest_submission_data, "submission_date", None),
    )
    fewest_errors_paediatric_diabetes_unit, error_number = (
        getattr(fewest_errors, "paediatric_diabetes_unit", None),
        getattr(fewest_errors, "error_count", None),
    )
    most_patients_paediatric_diabetes_unit, patient_number = (
        getattr(most_patients, "paediatric_diabetes_unit", None),
        getattr(most_patients, "patient_count", None),
    )
    most_visits_paediatric_diabetes_unit, visit_number = (
        getattr(most_visits, "paediatric_diabetes_unit", None),
        getattr(most_visits, "visits_per_patient", None),
    )

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
