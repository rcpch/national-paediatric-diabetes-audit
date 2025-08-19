# Python imports
from asgiref.sync import sync_to_async
from urllib.parse import urlparse
import logging

# Django imports
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse

from project.constants.feature_flags import FEATURE_FLAGS
from project.npda.general_functions.csv import csv_header
from ..general_functions.session import refresh_session_filters

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
async def home(request):
    """
    Home page view.
    Only verified users can access this page.
    """
    context = {}
    template = "home.html"
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
def view_preference(request):
    """
    HTMX callback from the button press in the view_preference.html template.
    """
    selected_pz_code = request.POST.get("pz_code_select_name", None)

    # includes a validation step
    refresh_session_filters(request, pz_code=selected_pz_code)

    return redirect_after_switcher(request)


@login_and_otp_required()
def audit_year(request):
    """
    View to change the audit year for the KPIs and submissions.
    """
    if request.method == "POST":
        audit_year = request.POST.get("audit_year_select_name", None)
        audit_year = int(audit_year) if audit_year else None

        refresh_session_filters(request, audit_year=audit_year)

        return redirect_after_switcher(request)

    response = render(
        request, template_name="partials/audit_year_select.html"
    )

    return response


@login_and_otp_required()
def celery_test_task(request):
    test_task.delay()

    return HttpResponse(status=204)


@login_and_otp_required()
def feature_flags(request):
    user_flags = request.session.get("feature_flags", [])

    if request.POST:
        for flag in FEATURE_FLAGS:
            if flag in request.POST and request.POST[flag] == "on":
                user_flags.append(flag)
            else:
                user_flags.remove(flag)

        request.session.update({"feature_flags": user_flags})

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
