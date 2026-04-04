# Python imports
import logging
from datetime import date

# Django imports
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect, render

from project.constants.feature_flags import FEATURE_FLAGS
from project.npda.general_functions.audit_period import get_audit_period_for_date
from project.npda.general_functions.csv import csv_header
from project.npda.general_functions.organisations_adapter import (
    paediatric_diabetes_units_for_user,
)
from project.npda.general_functions.session import get_user_feature_flags
from project.npda.models.audit_period import AuditPeriod
from project.npda.models.submission import Submission
from project.npda.tasks import test_task
from project.npda.views.npda_users import get_user_home_page

# RCPCH imports
from .decorators import check_data_permissions, login_and_otp_required

# Logging
logger = logging.getLogger(__name__)


@login_and_otp_required()
def home(request):
    """
    Home page view.
    Only verified users can access this page.
    """
    template = "home.html"
    return render(request=request, template_name=template, context={})


@login_and_otp_required()
def index(request):
    audit_period = AuditPeriod.objects.get_default_audit_period()
    url = get_user_home_page(audit_period.slug, request.user)
    return redirect(url)


@login_and_otp_required()
def new_home(request, audit_period):
    pdus = list(paediatric_diabetes_units_for_user(request.user))

    active_pdus = [pdu for pdu in pdus if pdu.active]

    inactive_pdus = []
    for pdu in pdus:
        if not pdu.active:
            if (
                request.user.is_rcpch_audit_team_member
                or Submission.objects.filter(
                    paediatric_diabetes_unit=pdu,
                    audit_period__slug=audit_period,
                    submission_active=True,
                ).exists()
            ):
                inactive_pdus.append(pdu)

    # Put the test PZ999 at the top of the list otherwise it's hard to find!
    sorted_active_pdus = sorted(
        active_pdus, key=lambda pdu: "" if pdu.pz_code == "PZ999" else pdu.pz_code
    )
    sorted_inactive_pdus = sorted(inactive_pdus, key=lambda pdu: pdu.pz_code)

    audit_period_obj = AuditPeriod.objects.get_audit_period_for_request(request)
    audit_periods = list(AuditPeriod.objects.all())

    if not request.user.is_rcpch_audit_team_member and not request.user.is_superuser:
        audit_periods = [p for p in audit_periods if p.is_visible]

    for p in audit_periods:
        p.selected = p.slug == audit_period_obj.slug

    # Determine the calendar-current audit period (based on today's date)
    today = date.today()
    current_start, _ = get_audit_period_for_date(today)
    try:
        current_audit_period_obj = AuditPeriod.objects.get(start_date=current_start)
    except AuditPeriod.DoesNotExist:
        current_audit_period_obj = None

    # Show new-year banner if we are in the first quarter (April–June) of a new audit period
    # and the user is viewing it but we're not yet looking at that period
    in_first_quarter = today.month in (4, 5, 6)
    viewing_current_period = (
        current_audit_period_obj is not None
        and audit_period_obj.slug == current_audit_period_obj.slug
    )
    show_new_year_banner = (
        in_first_quarter
        and current_audit_period_obj is not None
        and not viewing_current_period
    )

    # Check whether any of the user's PDUs have a submission in the currently-viewed period
    all_pdu_codes = [pdu.pz_code for pdu in active_pdus]
    has_any_submission_in_period = Submission.objects.filter(
        paediatric_diabetes_unit__pz_code__in=all_pdu_codes,
        audit_period=audit_period_obj,
        submission_active=True,
    ).exists()

    context = {
        "active_pdus": sorted_active_pdus,
        "inactive_pdus": sorted_inactive_pdus,
        "audit_periods": audit_periods,
        "selected_audit_period_display_name": audit_period_obj.display_name(),
        "selected_audit_period": audit_period_obj,
        "current_audit_period": current_audit_period_obj,
        "show_new_year_banner": show_new_year_banner,
        "has_any_submission_in_period": has_any_submission_in_period,
    }

    template = "new-home.html"
    return render(request=request, template_name=template, context=context)


@login_and_otp_required()
@check_data_permissions()
def download_template(request, audit_period, pdu):
    """
    Creates the template csv for users to fill out and upload into NPDA
    """

    # Allow overriding dataset_year via querystring (e.g. ?dataset_year=2026)
    dataset_year_param = request.GET.get("dataset_year")
    if dataset_year_param:
        try:
            dataset_year = int(dataset_year_param)
        except (ValueError, TypeError):
            logger.warning("Invalid dataset_year parameter: %s", dataset_year_param)
            dataset_year = 2021  # Default year
    is_jersey = pdu.pz_code == "PZ248"
    file = csv_header(is_jersey=is_jersey, dataset_year=dataset_year)

    return HttpResponse(
        file,
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="npda_template.csv"'},
    )


@login_and_otp_required()
def celery_test_task(request):
    test_task.delay()

    return HttpResponse(status=204)


@login_and_otp_required()
def feature_flags(request):
    if not (request.user.is_superuser or request.user.is_rcpch_audit_team_member):
        raise PermissionDenied("Feature previews are restricted to audit team.")
    if request.POST:
        user_flags = [
            flag
            for flag in FEATURE_FLAGS
            if flag in request.POST and request.POST[flag] == "on"
        ]
        request.user.feature_flags = user_flags
        request.user.save(update_fields=["feature_flags"])
        request.session.update({"feature_flags": user_flags})
    else:
        user_flags = get_user_feature_flags(request.user)
        request.session.update({"feature_flags": user_flags})

    all_flags = []

    for flag, details in FEATURE_FLAGS.items():
        all_flags.append(
            {
                "id": flag,
                "description": details["description"],
                "enabled": flag in user_flags,
            }
        )

    context = {
        "feature_flags": all_flags,
        "feedback_email": settings.SITE_CONTACT_EMAIL,
    }

    template_name = (
        "partials/feature_flag_form.html" if request.htmx else "feature_flags.html"
    )

    return render(request=request, template_name=template_name, context=context)
