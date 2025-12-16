# Python imports
from urllib.parse import urlparse
import logging

# Django imports
from django.conf import settings
from django.shortcuts import redirect, render
from django.http import HttpResponse

from project.constants.feature_flags import FEATURE_FLAGS
from project.npda.general_functions.csv import csv_header
from project.npda.general_functions.organisations_adapter import paediatric_diabetes_units_to_populate_select_field
from project.npda.views.npda_users import get_user_home_page

# RCPCH imports
from .decorators import login_and_otp_required, check_data_permissions

from project.npda.tasks import test_task
from project.npda.models.audit_period import AuditPeriod
from project.npda.models.paediatric_diabetes_unit import PaediatricDiabetesUnit

# Logging
logger = logging.getLogger(__name__)

# Temporary hack until everything is referenced by data url and we can remove this endpoint
def redirect_after_switcher(request):
    if request.htmx and request.htmx.current_url:
        path = urlparse(request.htmx.current_url).path

        if path.startswith("/period/"):
            audit_period = AuditPeriod.objects.get(
                start_date__year=request.session.get("selected_audit_year")
            )
            
            pz_code = request.session.get("pz_code", None)

            data_prefix = f"period/{audit_period.slug}/pdu/{pz_code}"

            rest_of_path = "/".join(path.split("/")[5:])

            return HttpResponse(
                status=204,
                headers={
                    "HX-Redirect": f"/{data_prefix}/{rest_of_path}",
                }
            )

    # Reload the page to apply the new view preference
    return HttpResponse(status=204, headers={"HX-Refresh": "true"})


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
    pdu_choices = paediatric_diabetes_units_to_populate_select_field(request.user)

    # Put the test PZ999 at the top of the list otherwise it's hard to find!
    pdu_choices.sort(key=lambda pdu: "" if pdu[0] == "PZ999" else pdu[0])

    audit_period = AuditPeriod.objects.get_audit_period_for_request(request)
    audit_periods = list(AuditPeriod.objects.all())

    if not request.user.is_rcpch_audit_team_member and not request.user.is_superuser:
        audit_periods = [p for p in audit_periods if p.is_visible]
    
    for p in audit_periods:
        p.selected = p.slug == audit_period.slug

    context = {
        "pdu_choices": pdu_choices,
        "audit_periods": audit_periods,
        "selected_audit_period_display_name": audit_period.display_name
    }

    template = "new-home.html"
    return render(request=request, template_name=template, context=context)


@login_and_otp_required()
@check_data_permissions()
def download_template(request, audit_period, pdu):
    """
    Creates the template csv for users to fill out and upload into NPDA
    """

    is_jersey = pdu.pz_code == "PZ248"
    file = csv_header(is_jersey=is_jersey)

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
    if request.POST:
        user_flags = [flag for flag in FEATURE_FLAGS if flag in request.POST and request.POST[flag] == "on"]
        request.session.update({"feature_flags": user_flags})
    else:
        user_flags = request.session.get("feature_flags", [])

    all_flags = []

    for flag, details in FEATURE_FLAGS.items():
        all_flags.append({
            "id": flag,
            "description": details["description"],
            "enabled": flag in user_flags
        })

    context = {
        "feature_flags": all_flags,
        "feedback_email": settings.SITE_CONTACT_EMAIL
    }

    template_name = "partials/feature_flag_form.html" if request.htmx else "feature_flags.html"

    return render(request=request, template_name=template_name, context=context)
