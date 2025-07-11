# Python imports
from asgiref.sync import sync_to_async
import logging

# Django imports
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse

from project.npda.general_functions.csv import csv_header
from ..general_functions.session import refresh_session_filters
from ..general_functions.view_preference import get_or_update_view_preference

# RCPCH imports
from .decorators import login_and_otp_required

from project.npda.tasks import test_task

# Logging
logger = logging.getLogger(__name__)


@login_and_otp_required()
async def home(request):
    """
    Home page view.
    Only verified users can access this page.
    """
    pdu_choices = request.session.get("pdu_choices", [])
    pdu_choices.sort(key=lambda pdu: pdu[0])

    context = {
        "pdu_choices": pdu_choices,
    }
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
    Called from:
      - HTMX callback from the switcher in view_preference.html
      - Following the PDU specific links (upload data etc) from the home page
    """
    next_page = request.GET.get("next_page", None)

    def get_param(name):
        return request.GET.get(name, request.POST.get(name, None))

    view_preference_selection = get_param("view_preference")
    selected_pz_code = get_param("pz_code_select_name")

    view_preference = get_or_update_view_preference(
        request.user, view_preference_selection
    )

    # includes a permission check
    refresh_session_filters(request, pz_code=selected_pz_code)

    if next_page:
        # Use reverse to avoid an open redirect
        return redirect(reverse(next_page))

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