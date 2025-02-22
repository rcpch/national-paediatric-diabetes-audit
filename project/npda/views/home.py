# Python imports
import json
import logging
import io

# Django imports
from django.apps import apps
from django.contrib import messages
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.conf import settings


# Third party imports
from django_htmx.http import trigger_client_event
from celery.result import AsyncResult, GroupResult

from project.npda.general_functions.csv import csv_parse, csv_header
from project.npda.general_functions.csv.csv_upload_celery import csv_upload
from ..forms.upload import UploadFileForm
from ..general_functions.session import refresh_session_filters
from ..general_functions.view_preference import get_or_update_view_preference
from ..general_functions.csv.progress_recorder import ProgressTracker

# RCPCH imports
from .decorators import login_and_otp_required

# Logging
logger = logging.getLogger(__name__)


@login_and_otp_required()
def home(request):
    """
    Home page view - contains the upload form.
    Only verified users can access this page.
    """
    if request.session.get("can_upload_csv") is False:
        # If the user does not have permission to upload csvs, redirect them to the submissions page
        return redirect("dashboard")

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
                return redirect("home")

            audit_year = request.session.get("selected_audit_year")

            # CSV is valid, parse any errors and store the data in the tables.
            grouped_tasks_id = csv_upload(
                user=request.user,
                dataframe=parsed_csv.df,
                csv_file_name=user_csv_filename,
                csv_file_bytes=user_csv_bytes,
                pz_code=pz_code,
                audit_year=audit_year,
            )

            # log user activity
            VisitActivity = apps.get_model("npda", "VisitActivity")
            try:
                VisitActivity.objects.create(
                    activity=8,
                    ip_address=request.META.get("REMOTE_ADDR"),
                    npdauser=request.user,
                )  # uploaded csv - activity 8
            except Exception as e:
                logger.error(f"Failed to log user activity: {e}")

            # update the session fields - this stores that the user has uploaded a csv and disables the ability to use the questionnaire
            # await sync_to_async(refresh_session_filters)(request)
            refresh_session_filters(request)

            return redirect("task_status", grouped_tasks_id=grouped_tasks_id)
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


def download_template(request, region):
    """
    Creates the template csv for users to fill out and upload into NPDA
    """
    if region == "england_wales":
        file = csv_header()
    elif region == "jersey":
        file = csv_header(is_jersey=True)
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


def task_status(request, grouped_tasks_id):
    """
    HTMX callback to get the status of a Celery task.
    """

    task_results = GroupResult.restore(grouped_tasks_id)
    if task_results is None:
        task_results = GroupResult(grouped_tasks_id)

    all_successful = True
    progress_data = []

    for task in task_results.results:
        progress_tracker = ProgressTracker(task.id)
        errors = 0
        if task.state == "SUCCESS":
            progress_data.append(progress_tracker.get_progress())
            errors_by_row_index = task.result
            if errors_by_row_index:
                errors = len(errors_by_row_index.items())
                progress_tracker.set_errors(errors)

        elif task.state == "FAILURE":
            all_successful = False
            progress_data.append({"state": task.state, "task_id": task.task_id})
            messages.error(
                request=request,
                message="An error occurred while processing some of the rows of the CSV file. Please try again.",
            )
            return redirect("home")
        else:
            all_successful = False
            progress_data.append(progress_tracker.get_progress())

    if all_successful:
        messages.success(
            request=request, message="Submission completed. There were no errors."
        )
        if request.htmx:
            response = HttpResponse(status=204)
            response["HX-Redirect"] = "/patients"
            return response
        else:
            return redirect("patients")
    else:
        if request.htmx:
            total = len(progress_data)
            value = len(
                [task for task in task_results.results if task.state == "SUCCESS"]
            )
            return render(
                request=request,
                template_name="partials/page_elements/progress.html",
                context={
                    "grouped_tasks_id": grouped_tasks_id,
                    "state": task.state,
                    "progress_data": progress_data,
                    "total": total,
                    "value": value,
                    "percentage": int((value / total) * 100),
                },
            )
        else:
            print("Non-HTMX request")
            return render(
                request=request,
                template_name="progress_temp.html",
                context={
                    "grouped_tasks_id": grouped_tasks_id,
                    "state": task.state,
                    "progress_data": progress_data,
                },
            )
