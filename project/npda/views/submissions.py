# Python imports
import json
import logging
import io
from typing import Any, Iterable
from datetime import date
from asgiref.sync import sync_to_async

# Django imports
from django.apps import apps
from django.contrib import messages
from django.db.models import Count, Case, When, F, Value
from django.db.models.functions import Concat
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import ListView

from project.npda.views.decorators import login_and_otp_required

# RCPCH imports
from .mixins import CheckCurrentAuditYearMixin, LoginAndOTPRequiredMixin
from ..models import Submission, VisitActivity
from ..forms.upload import UploadFileForm
from ..general_functions.session import refresh_session_filters
from ..general_functions.csv import (
    download_csv,
    download_xlsx,
    csv_parse,
    csv_upload
)


# Logging
logger = logging.getLogger(__name__)


class SubmissionsListView(
    LoginAndOTPRequiredMixin, CheckCurrentAuditYearMixin, ListView
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
        requested_active_submission = self.object_list.filter(
            submission_active=True,
            audit_year=self.request.session.get("selected_audit_year"),
            paediatric_diabetes_unit__pz_code=self.request.session.get("pz_code"),
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

        return context

    def get(self, request, *args, **kwargs):
        """
        Handle the HTMX GET request.
        """
        self.object_list = self.get_queryset().order_by("-submission_date")
        context = self.get_context_data(object_list=self.object_list)
        template = self.template_name

        if request.htmx:
            # If the request is an HTMX request from the PDU selector or Audit Year selector, returns the partial template
            # Otherwise, returns the full template
            # The partial template is used to update the submission history table when a new PDU is selected
            # This is done with a custom htmx trigger in the PDU selector
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
        button_name = request.POST.get("submit-data")
        if button_name == "delete-data":
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
            submission = Submission.objects.filter(
                pk=request.POST.get("audit_id")
            ).get()
            return download_csv(request, submission.id)

        if button_name == "download-report":
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
async def upload_csv(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        user_csv = request.FILES["csv_upload"]
        user_csv_filename = user_csv.name
        # We are eventually storing the CSV file as a BinaryField so have to hold it in memory
        user_csv_bytes = user_csv.read()

        pz_code = request.session.get("pz_code")
        is_jersey = pz_code == "PZ248"
        if request.session.get("can_upload_csv") is True:
            # check to see if the CSV is valid - cannot accept CSVs with no header. All other header errors are non-lethal but are reported back to the user
            try:
                parsed_csv = csv_parse(io.BytesIO(user_csv_bytes), is_jersey=is_jersey)
            except ValueError as e:
                messages.error(
                    request=request,
                    message=f"Invalid CSV format: {e}",
                )
                return redirect("home")

            if (
                parsed_csv.missing_columns
                or parsed_csv.additional_columns
                or parsed_csv.duplicate_columns
            ):
                message = "Invalid CSV format."
                if parsed_csv.missing_columns:
                    message += (
                        f" Missing columns: [{", ".join(parsed_csv.missing_columns)}]"
                    )
                if parsed_csv.additional_columns:
                    message += f" Unexpected columns: [{", ".join(parsed_csv.additional_columns)}]"
                if parsed_csv.duplicate_columns:
                    message += f" Duplicate columns: [{", ".join(parsed_csv.additional_columns)}]"
                messages.error(
                    request=request,
                    message=message,
                )
                return render(request, "upload_csv/file_upload.html")

            audit_year = request.session.get("selected_audit_year")

            # CSV is valid, parse any errors and store the data in the tables.
            errors_by_row_index = await csv_upload(
                user=request.user,
                dataframe=parsed_csv.df,
                csv_file_name=user_csv_filename,
                csv_file_bytes=user_csv_bytes,
                pdu_pz_code=pz_code,
                audit_year=audit_year,
            )
            # log user activity
            try:
                await VisitActivity.objects.acreate(
                    activity=8,
                    ip_address=request.META.get("REMOTE_ADDR"),
                    npdauser=request.user,
                )  # uploaded csv - activity 8
            except Exception as e:
                logger.error(f"Failed to log user activity: {e}")

            # update the session fields - this stores that the user has uploaded a csv and disables the ability to use the questionnaire
            await sync_to_async(refresh_session_filters)(request)

            if errors_by_row_index:
                messages.error(
                    request=request,
                    message=f"CSV has been uploaded, but errors were found in {len(errors_by_row_index.items())} rows. Please check the data quality report for details.",
                )
            else:
                messages.success(
                    request=request,
                    message="Submission completed. There were no errors.",
                )
            return redirect("patients")
        else:
            # If the user does not have permission to upload csvs, redirect them to the dashboard page
            messages.error(
                request=request,
                message=f"You have do not have permission to upload csvs for {pz_code}.",
            )
            return redirect("dashboard")

    return render(request, "upload_csv/file_upload.html")
