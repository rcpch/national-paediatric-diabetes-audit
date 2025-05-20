# Python imports
from asgiref.sync import sync_to_async
import datetime
import logging
import json
import io

from datetime import date


# Django imports
from django.apps import apps
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import HttpResponse
from django.conf import settings
from django.utils import timezone


# HTMX imports
from django_htmx.http import trigger_client_event

from project.npda.general_functions.csv import csv_upload, csv_parse, csv_header
from project.npda.general_functions.csv import (
    csv_upload,
    csv_parse,
    csv_header,
    create_csv_submission,
    tidy_up_old_submissions
)
from ..forms.upload import UploadFileForm
from ..general_functions.session import refresh_session_filters
from ..general_functions.view_preference import get_or_update_view_preference
from ..models import PaediatricDiabetesUnit, AuditPeriod
from ..tasks import upload_csv_task

# RCPCH imports
from .decorators import login_and_otp_required

from project.npda.tasks import test_task

# Logging
logger = logging.getLogger(__name__)


@login_and_otp_required()
async def home(request):
    """
    Home page view - contains the upload form.
    Only verified users can access this page.
    """
    if request.session.get("can_upload_csv") is False:
        # If the user does not have permission to upload csvs, redirect them to the submissions page
        return redirect("dashboard")

    if request.method == "POST":
        has_perm = await sync_to_async(request.user.has_perm)("npda.can_submit_csv")
        if not has_perm:
            raise PermissionDenied("You do not have permission to upload CSV files.")
        
        form = UploadFileForm(request.POST, request.FILES)

        user_csv = request.FILES["csv_upload"]
        user_csv_filename = user_csv.name
        # We are eventually storing the CSV file as a BinaryField so have to hold it in memory
        user_csv_bytes = user_csv.read()

        pz_code = request.session.get("pz_code")
        is_jersey = pz_code == "PZ248"

        # TODO MRB: check pdu is active and I'm not a superuser?
        pdu = await PaediatricDiabetesUnit.objects.aget(pz_code=pz_code)

        if request.session.get("can_upload_csv") is True:
            # check to see if the CSV is valid - cannot accept CSVs with no header. All other header errors are non-lethal but are reported back to the user
            try:
                parsed_csv = csv_parse(io.BytesIO(user_csv_bytes))
            except ValueError as e:
                print(f"!! {dir(e)}")
                messages.error(
                    request=request,
                    message=f"Invalid CSV format: {e}",
                )
                return redirect("upload_csv")

            missing_columns = parsed_csv.missing_columns
            if not parsed_csv.identifier_column:
                missing_columns.append("Unique Reference Number" if is_jersey else "NHS Number")

            if (
                missing_columns
                or parsed_csv.additional_columns
                or parsed_csv.duplicate_columns
            ):
                message = "Invalid CSV format."
                if missing_columns:
                    message += (
                        f" Missing columns: [{", ".join(missing_columns)}]"
                    )
                if parsed_csv.additional_columns:
                    message += f" Unexpected columns: [{", ".join(parsed_csv.additional_columns)}]"
                if parsed_csv.duplicate_columns:
                    message += f" Duplicate columns: [{", ".join(parsed_csv.additional_columns)}]"
                messages.error(
                    request=request,
                    message=message,
                )
                return redirect("upload_csv")
            
            if parsed_csv.identifier_column == "Unique Reference Number" and not is_jersey:
                messages.error(
                    request=request,
                    message="CSV file must use NHS number as the identifier column unless uploading for Jersey"
                )
                return redirect("upload_csv")

            audit_period = await sync_to_async(AuditPeriod.objects.get_audit_period_for_request)(request)
            if not audit_period.is_open and not (request.user.is_superuser or request.user.is_rcpch_audit_team_member):
                raise PermissionDenied(f"Upload is closed for {audit_period.audit_year()}.")

            new_submission = await create_csv_submission(
                pdu=pdu,
                audit_year=audit_period.audit_year(),
                csv_file_bytes=user_csv_bytes,
                csv_file_name=user_csv_filename,
                # The celery task will flip it to active once complete
                submission_active=False,
                user=request.user,
                ip_address=request.META.get("REMOTE_ADDR"),
            )

            upload_csv_task.delay(new_submission.id)

            # update the session fields - this stores that the user has uploaded a csv and disables the ability to use the questionnaire
            await sync_to_async(refresh_session_filters)(request, csv_upload=True)
            
            return redirect("upload-csv-in-progress")
        else:
            # If the user does not have permission to upload csvs, redirect them to the dashboard page
            messages.error(
                request=request,
                message=f"You have do not have permission to upload csvs for {pz_code}.",
            )
            return redirect("dashboard")

    else:
        form = UploadFileForm()

    context = {"file_uploaded": False, "form": form}
    template = "home.html"
    return render(request=request, template_name=template, context=context)


def download_template(request):
    """
    Creates the template csv for users to fill out and upload into NPDA
    """

    is_jersey = request.session.get("pz_code") == "PZ248"
    file = csv_header(is_jersey=is_jersey)

    return HttpResponse(
        file,
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="npda_template.csv"'},
    )


def view_preference(request):
    """
    HTMX callback from the button press in the view_preference.html template.
    """

    view_preference_selection = request.POST.get("view_preference", None)
    view_preference = get_or_update_view_preference(
        request.user, view_preference_selection
    )
    selected_pz_code = request.POST.get("pz_code_select_name", None)

    # includes a validation step
    refresh_session_filters(request, pz_code=selected_pz_code)

    # Reload the page to apply the new view preference
    return HttpResponse(status=204, headers={"HX-Refresh": "true"})


@login_and_otp_required()
def audit_year(request):
    """
    View to change the audit year for the KPIs and submissions.
    """
    if request.method == "POST":
        audit_year = request.POST.get("audit_year_select_name", None)
        audit_year = int(audit_year) if audit_year else None

        refresh_session_filters(request, audit_year=audit_year)

        # Reload the page to apply the new view preference
        return HttpResponse(status=204, headers={"HX-Refresh": "true"})

    context = {
        "audit_years": request.session.get("audit_years"),
        "selected_audit_year": request.session.get("selected_audit_year"),
    }

    response = render(
        request, template_name="partials/audit_year_select.html", context=context
    )

    return response


@login_and_otp_required()
def celery_test_task(request):
    test_task.delay()

    return HttpResponse(status=204)