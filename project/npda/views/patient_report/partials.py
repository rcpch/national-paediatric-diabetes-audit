import logging
from datetime import date


# Django imports
from django.http import HttpResponseBadRequest

# Django imports
from django.shortcuts import render

from project.npda.kpi_class.kpis import CalculateKPIS
from project.npda.views.patient_report.helpers import (
    get_pt_level_table_data,
)
from project.npda.views.patient_report.template_data import KPI_CATEGORY_ATTR_MAP, TEXT
from project.npda.views.decorators import login_and_otp_required

logger = logging.getLogger(__name__)


@login_and_otp_required()
def get_patient_level_report_partial(request):

    if not request.htmx:
        return HttpResponseBadRequest("This view is only accessible via HTMX")

    pt_level_menu_tab_selected = request.GET.get("selected")

    # State vars
    # Colour the selected menu tab
    highlight = {f"{key}": key == pt_level_menu_tab_selected for key in TEXT.keys()}

    selected_data: dict = TEXT[pt_level_menu_tab_selected]

    # Gather the selected category's data

    # First need to get the relevant calculations
    pz_code = request.session.get("pz_code")

    selected_audit_year = int(request.session.get("selected_audit_year"))
    # TODO: remove min clamp once available audit year from preference filter sorted
    selected_audit_year = max(selected_audit_year, 2024)
    calculation_date = date(year=selected_audit_year, month=5, day=1)

    calculate_kpis = CalculateKPIS(calculation_date=calculation_date, return_pt_querysets=True)

    # Set relevant patients
    calculate_kpis.set_patients_for_calculation(pz_codes=[pz_code])

    # Run the relevant subset of calculations
    selected_kpis = KPI_CATEGORY_ATTR_MAP[pt_level_menu_tab_selected]
    kpi_calculations_object = calculate_kpis._calculate_kpis(selected_kpis)

    try:
        selected_table_headers, selected_table_data = get_pt_level_table_data(
            category=pt_level_menu_tab_selected,
            calculate_kpis_object=calculate_kpis,
            kpi_calculations_object=kpi_calculations_object,
        )
    except Exception as e:
        logger.error(
            f"Error getting pt_level_table_data for {pt_level_menu_tab_selected=} {e=}",
            exc_info=True,
        )
        # messages.error(request, f"Error getting data!")

        selected_table_headers = []
        selected_table_data = []

    context = {
        "text": selected_data,
        "selected": pt_level_menu_tab_selected,
        "highlight": highlight,
        "table_data": {
            "headers": selected_table_headers,
            "row_data": selected_table_data,
            "ineligible_hover_reason": selected_data.get("ineligible_hover_reason", {}),
        },
    }

    return render(
        request,
        template_name="patient_report/pt_level_report_table_container_partial.html",
        context=context,
    )

def get_pt_level_report_table(request):

    if not request.htmx:
        return HttpResponseBadRequest("This view is only accessible via HTMX")
    
    logger.info("get_pt_level_report_table")

    return render(request, template_name="patient_report/health_checks_table_partial.html")
