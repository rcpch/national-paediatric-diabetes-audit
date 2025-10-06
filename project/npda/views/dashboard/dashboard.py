# Python imports
import logging
from datetime import datetime, date

from django.shortcuts import render

from project.npda.general_functions.quarter_for_date import retrieve_quarter_for_date
from project.npda.general_functions.breadcrumbs import data_breadcrumbs
from project.npda.kpi_class.kpis import CalculateKPIS
from project.npda.views.decorators import login_and_otp_required, check_data_permissions

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
        days_remaining_until_audit_end_date = (audit_period.end_date - current_date).days
    elif current_date > audit_period.end_date:
        # Past audit period
        current_quarter = None
        days_remaining_until_audit_end_date = None
    else:
        # Current audit period
        current_quarter = retrieve_quarter_for_date(current_date)
        days_remaining_until_audit_end_date = (audit_period.end_date - current_date).days

    context = {
        "scatter_plot_select_list": _scatter_plot_select_list("new_diagnoses"),
        "pdu_object": pdu,
        "current_date": calculation_date,
        "current_datetime": current_datetime,
        "current_quarter": current_quarter,
        "audit_period": audit_period,
        "days_remaining_until_audit_end_date": days_remaining_until_audit_end_date,
        # TODO: this should be an enum but we're currently not doing benchmarking so can update
        # at that point
        "aggregation_level": "pdu",
        "breadcrumbs": data_breadcrumbs(pdu, audit_period, [
            ("Unit Report", "pdu-dashboard")
        ])
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