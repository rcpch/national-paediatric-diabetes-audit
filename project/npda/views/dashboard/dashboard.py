# Python imports
import json
import logging
from datetime import date, datetime, timedelta

from django.shortcuts import render
from django.urls import reverse

from project.npda.general_functions.audit_period import get_quarters_for_audit_period
from project.npda.general_functions.breadcrumbs import data_breadcrumbs
from project.npda.general_functions.patient_report.queries import (
    count_eligible_patients,
    count_new_diagnoses_by_quarter,
)
from project.npda.general_functions.quarter_for_date import retrieve_quarter_for_date
from project.npda.models.audit_period import AuditPeriod
from project.npda.views.decorators import check_data_permissions, login_and_otp_required

# LOGGING
logger = logging.getLogger(__name__)


@login_and_otp_required()
@check_data_permissions()
def dashboard(request, audit_period, pdu):
    """
    Dashboard view for the KPIs.
    """
    template = "dashboard.html"
    if request.htmx:
        template = "dashboard/dashboard_base.html"

    current_date = date.today()
    current_datetime = datetime.now()

    calculation_date = audit_period.kpi_calculation_date()

    if audit_period.start_date > current_date:
        # Future audit period - likely no data yet but you can still select it
        current_quarter = None
        days_remaining_until_audit_end_date = (
            audit_period.end_date - current_date
        ).days
    elif current_date > audit_period.end_date:
        # Past audit period
        current_quarter = None
        days_remaining_until_audit_end_date = None
    else:
        # Current audit period
        current_quarter = retrieve_quarter_for_date(current_date)
        days_remaining_until_audit_end_date = (
            audit_period.end_date - current_date
        ).days

    no_eligible_patients = count_eligible_patients(pdu, audit_period)

    # new diagnoses split by quarter
    new_diagnosis_per_quarter_value_counts_pct = count_new_diagnoses_by_quarter(
        pdu, audit_period
    )

    # Determine whether the user is viewing a closed period when a newer one is now current.
    # This banner is only meaningful for non-htmx (full page) loads.
    today = current_date
    current_audit_period = AuditPeriod.objects.filter(
        start_date__lte=today,
        end_date__gte=today,
    ).first()
    viewing_stale_period = (
        current_audit_period is not None and current_audit_period.pk != audit_period.pk
    )
    # Q1 of the current audit period. If today falls within it and the viewed period
    # is the one that ended immediately before the current period started, submissions
    # are still accepted for it.
    in_first_quarter = False
    if current_audit_period is not None:
        q1_start, q1_end = get_quarters_for_audit_period(
            current_audit_period.start_date, current_audit_period.end_date
        )[0]
        in_first_quarter = q1_start <= today <= q1_end
    previous_period_still_accepts = (
        viewing_stale_period
        and in_first_quarter
        and current_audit_period is not None
        and audit_period.end_date == current_audit_period.start_date - timedelta(days=1)
    )
    upload_url_for_current_period = (
        reverse(
            "pdu-upload-csv",
            kwargs={
                "audit_period": current_audit_period.slug,
                "pz_code": pdu.pz_code,
            },
        )
        if viewing_stale_period
        else None
    )

    context = {
        "scatter_plot_select_list": _scatter_plot_select_list("new_diagnoses"),
        "pdu_object": pdu,
        "current_date": calculation_date,
        "current_datetime": current_datetime,
        "current_quarter": current_quarter,
        "audit_period": audit_period,
        "days_remaining_until_audit_end_date": days_remaining_until_audit_end_date,
        "charts": {
            "new_diagnoses_per_quarter_value_counts_pct": {
                "no_eligible_patients": no_eligible_patients == 0,
                "data": json.dumps(new_diagnosis_per_quarter_value_counts_pct),
            }
        },
        # TODO: this should be an enum but we're currently not doing benchmarking so can update
        # at that point
        "aggregation_level": "pdu",
        "breadcrumbs": data_breadcrumbs(
            pdu, audit_period, [("Unit Report", "pdu-dashboard")]
        ),
        "viewing_stale_period": viewing_stale_period,
        "previous_period_still_accepts": previous_period_still_accepts,
        "current_audit_period": current_audit_period,
        "upload_url_for_current_period": upload_url_for_current_period,
    }

    return render(request, template_name=template, context=context)


def _scatter_plot_select_list(button_name_selected: str):
    """
    Keeps track of which filter buttons are selected in the scatter plot
    """
    scatter_buttons = [
        {
            "name": "new_diagnoses",
            "selected": button_name_selected == "new_diagnoses",
            "enabled": True,
            "title": "New diagnoses",
        },
        {
            "name": "new_admissions",
            "selected": button_name_selected == "new_admissions",
            "enabled": True,
            "title": "Hospital Admissions",
        },
        {
            "name": "transitioned_to_adult_service",
            "selected": button_name_selected == "transitioned_to_adult_service",
            "enabled": True,
            "title": "Transitioned",
        },
    ]
    return scatter_buttons
