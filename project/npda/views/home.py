# Python imports
from asgiref.sync import sync_to_async
import logging

# Django imports
from django.shortcuts import render
from django.http import HttpResponse

from project.npda.general_functions.csv import csv_header
from ..general_functions.session import refresh_session_filters
from ..general_functions.view_preference import get_or_update_view_preference

# RCPCH imports
from .decorators import login_and_otp_required, check_data_permissions

from project.npda.tasks import test_task

# Logging
logger = logging.getLogger(__name__)


@login_and_otp_required()
async def home(request):
    """
    Home page view.
    Only verified users can access this page.
    """
    context = {}
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
