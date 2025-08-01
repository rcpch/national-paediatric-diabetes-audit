# Python imports
import json
import logging
from datetime import date

from django.apps import apps
from django.contrib import messages
from django.shortcuts import render

from project.npda.general_functions.audit_period import audit_period_for_audit_year
from project.npda.general_functions.quarter_for_date import retrieve_quarter_for_date
from project.npda.kpi_class.kpis import CalculateKPIS
from project.npda.models.paediatric_diabetes_unit import (
    PaediatricDiabetesUnit as PaediatricDiabetesUnitClass,
)
from project.npda.models.patient import Patient
from project.npda.models.audit_period import AuditPeriod
from project.npda.views.decorators import login_and_otp_required

# LOGGING
logger = logging.getLogger(__name__)


@login_and_otp_required()
def dashboard(request):
    """
    Dashboard view for the KPIs.
    """
    template = "dashboard.html"
    if request.htmx:
        template = "dashboard/dashboard_base.html"
    pz_code = request.session.get("pz_code")

    PaediatricDiabetesUnit: PaediatricDiabetesUnitClass = apps.get_model(
        "npda", "PaediatricDiabetesUnit"
    )
    try:
        pdu = PaediatricDiabetesUnit.objects.get(pz_code=pz_code)
    except PaediatricDiabetesUnit.DoesNotExist:
        messages.error(
            request=request,
            message=f"Paediatric Diabetes Unit with PZ code {pz_code} does not exist",
        )
        return render(request, "dashboard.html")

    audit_period = AuditPeriod.objects.get_audit_period_for_request(request)
    
    current_date = date.today()
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

    calculate_kpis = CalculateKPIS(
        calculation_date=calculation_date, return_pt_querysets=True
    )

    kpi_calculations_object = calculate_kpis.calculate_kpis_for_pdus(pz_codes=[pz_code])

    # From this, gather specific chart data required

    # new diagnoses
    new_diagnosis_per_quarter_value_counts_pct = (
        calculate_kpis.calculate_kpi_2_total_new_diagnoses_stratified_by_quarter()
    )

    context = {
        "scatter_plot_select_list": _scatter_plot_select_list("new_diagnoses"),
        "pdu_object": pdu,
        # "pdu_lead_organisation": pdu_lead_organisation,
        "kpi_calculations_object": kpi_calculations_object,
        "current_date": calculation_date,
        "current_quarter": current_quarter,
        "days_remaining_until_audit_end_date": days_remaining_until_audit_end_date,
        "charts": {
            "new_diagnoses_per_quarter_value_counts_pct": {
                "no_eligible_patients": kpi_calculations_object[
                    "calculated_kpi_values"
                ]["kpi_1_total_eligible"]["total_eligible"]
                == 0,
                "data": json.dumps(new_diagnosis_per_quarter_value_counts_pct),
            }
        },
        # TODO: this should be an enum but we're currently not doing benchmarking so can update
        # at that point
        "aggregation_level": "pdu",
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