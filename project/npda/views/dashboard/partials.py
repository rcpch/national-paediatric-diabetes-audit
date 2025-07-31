import json
import logging
from datetime import date

import plotly.graph_objects as go
import plotly.io as pio
from django.apps import apps
from django.contrib import messages

# Django imports
from django.http import HttpResponseBadRequest

# Django imports
from django.shortcuts import render

import project.constants.colors as colors
from project.npda.general_functions.audit_period import audit_period_for_audit_year
from project.npda.general_functions.map import (
    generate_dataframe_and_aggregated_distance_data_from_cases,
    generate_distance_from_organisation_scatterplot_figure,
    get_children_by_pdu_audit_year,
)
from project.npda.general_functions.rcpch_nhs_organisations import (
    fetch_organisation_by_ods_code,
)
from project.npda.kpi_class.kpis import CalculateKPIS
from project.npda.models.paediatric_diabetes_unit import (
    PaediatricDiabetesUnit as PaediatricDiabetesUnitClass,
)
from project.npda.models.submission import Submission
from project.npda.models.audit_period import AuditPeriod
from project.npda.models.paediatric_diabetes_unit import PaediatricDiabetesUnit
from project.npda.views.decorators import login_and_otp_required

logger = logging.getLogger(__name__)

DEFAULT_CHART_HTML_HEIGHT = "18rem"


@login_and_otp_required()
def get_map_chart_partial(request):

    if not request.htmx:
        return HttpResponseBadRequest("This view is only accessible via HTMX")

    pdu = PaediatricDiabetesUnit.objects.get_pdu_for_request(request)
    audit_period = AuditPeriod.objects.get_audit_period_for_request(request)
    submission = Submission.objects.get_submission_for_request(pdu, audit_period)

    if not submission:
        return render(
            request,
            "dashboard/map_chart_partial.html",
            {"info": "No patient data yet"},
        )

    lead_organisation_ods_code = submission.paediatric_diabetes_unit.lead_organisation_ods_code

    try:
        pdu_lead_organisation = fetch_organisation_by_ods_code(
            ods_code=lead_organisation_ods_code
        )
    except:
        raise ValueError(
            f"Lead organisation for PDU {lead_organisation_ods_code=} not found"
        )

    try:
        # these are all registered patients for the current cohort at the selected organisation to be plotted in the map
        patients_to_plot = get_children_by_pdu_audit_year(submission,pdu_lead_organisation)

        # aggregated distances (mean, median, max, min) that patients have travelled to the selected organisation
        aggregated_distances, patient_distances_dataframe = (
            generate_dataframe_and_aggregated_distance_data_from_cases(
                filtered_cases=patients_to_plot
            )
        )

        # generate scatterplot of patients by distance from the selected organisation
        scatterplot_of_cases_for_selected_organisation_fig = (
            generate_distance_from_organisation_scatterplot_figure(
                geo_df=patient_distances_dataframe,
                pdu_lead_organisation=pdu_lead_organisation,
                paediatric_diabetes_unit=submission.paediatric_diabetes_unit,
            )
        )

        return render(
            request,
            template_name="dashboard/map_chart_partial.html",
            context={
                "chart_html": pio.to_html(
                    scatterplot_of_cases_for_selected_organisation_fig,
                    full_html=False,
                    include_plotlyjs=False,
                    config={"displayModeBar": True},
                ),
                "aggregated_distances": aggregated_distances,
            },
        )

    except Exception as e:
        logger.error("Error generating map chart", exc_info=True)
        return render(
            request,
            "dashboard/map_chart_partial.html",
            {"error": "Something went wrong!"},
        )


@login_and_otp_required()
def get_metric_scatter_plot(request):
    """HTMX view that accepts a GET request with an object of waffle labels and percentages,
    returning a waffle chart rendered.

    Must have request.GET data -> template responsible for handling empty data"""

    try:

        if not request.htmx:
            return HttpResponseBadRequest("This view is only accessible via HTMX")

        if request.method == "POST":
            selected_chart = request.POST["scatter_plot_select"]
            calculation_date = AuditPeriod.objects.get_audit_period_for_request(request).kpi_calculation_date()
            data, title, tooltip_text = get_selected_chart_data(
                selected_chart, calculation_date, request.session.get("pz_code")
            )

        if request.method == "GET":
            if not (request_data := request.GET.get("data", None)):
                return HttpResponseBadRequest("No data provided")

            # Fetch data from query parameters
            # if data is None:
            data = json.loads(request_data)
            title = "All new diabetes diagnoses by quarter"
            tooltip_text = "Numbers of patients newly diagnosed with any type of diabetes each quarter. The plots in blue reflect only new diagnoses in that quarter, the plots in grey are cumulative totals."

        # Extracting data
        quarters = [f"Q{q}" for q in data]
        percentages = [data[q]["pct"] for q in data]
        passed = [data[q]["total_passed"] for q in data]
        cumulative_sum = 0
        incremental_passed = [
            (cumulative_sum := cumulative_sum + data[q]["total_passed"]) for q in data
        ]
        eligible = [data[q]["total_eligible"] for q in data]
        all_colors = [colors.RCPCH_LIGHT_BLUE for _ in data]
        # highlight the last quarter
        all_colors[-1] = colors.RCPCH_PINK

        # Create scatter plot
        fig = go.Figure()

        # cumulative totals
        fig.add_trace(
            go.Scatter(
                x=quarters,
                y=incremental_passed,
                marker=dict(
                    color=colors.RCPCH_LIGHT_GREY,  # Change to desired color
                    line=dict(color=colors.RCPCH_LIGHT_GREY, width=1),  # Add border
                    symbol="square",
                    size=12,
                ),
                hovertemplate="<b>Running Total: <i>%{y}</i> children in %{x}</b><extra></extra>",
                name="Cumulative Total",
            ),
        )
        # totals by quarter
        fig.add_trace(
            go.Scatter(
                x=quarters,
                y=passed,
                mode="lines+markers",
                marker=dict(
                    size=12,
                    color=all_colors,
                    symbol="square",
                ),
                line=dict(color=colors.RCPCH_LIGHT_BLUE),
                hovertemplate="Quarter total: <b><i>%{y}</i> children in %{x}</b><extra></extra>",
                name="Quarterly Total",
            ),
        )

        # Add annotation for last quarter
        last_passed = passed[-1]
        # Offset below point if penultimate point higher than final point
        Y_SHIFT = 20
        if len(passed) > 1 and passed[-2] >= last_passed:
            # If the final point is < 10, don't offset below as goes off the chart
            yshift = -Y_SHIFT if last_passed > (Y_SHIFT) else Y_SHIFT
        else:
            # Don't need to account for going off the chart at top as added space
            yshift = Y_SHIFT
        fig.add_annotation(
            x=quarters[-1],
            y=passed[-1],
            text=f"{passed[-1]} children in {quarters[-1]}",
            showarrow=False,
            font=dict(color=colors.RCPCH_PINK, size=12),
            yshift=yshift,
        )

        # Layout adjustments
        fig.update_layout(
            xaxis=dict(title="Quarter", range=[-0.5, len(quarters) - 0.5]),
            yaxis=dict(title="Number of children"),
            showlegend=True,
            template="simple_white",  # Clean grid style
            margin=dict(l=0, r=0, t=0, b=0),
        )

        chart_html = fig.to_html(
            full_html=False,
            include_plotlyjs=False,
            config={
                "displayModeBar": False,
            },
            default_height="12rem",
        )

        return render(
            request,
            "dashboard/metric_scatter_plot_partial.html",
            {
                "chart_html": chart_html,
                "chart_title": title,
                "tooltip_text": tooltip_text,
            },
        )
    except Exception as e:
        logger.error("Error generating metric scatter plot", exc_info=True)
        return render(
            request,
            "dashboard/metric_scatter_plot_partial.html",
            {"error": "Something went wrong!"},
        )


@login_and_otp_required()
def get_new_diagnoses_partial(request):
    """HTMX view that returns the number of new diagnoses for the current submission"""

    # Get new diagnoses this submission
    pz_code = request.session.get("pz_code")

    calculation_date = AuditPeriod.objects.get_audit_period_for_request(request).kpi_calculation_date()

    calculate_kpis = CalculateKPIS(
        calculation_date=calculation_date, return_pt_querysets=False
    )

    calculate_kpis.set_patients_for_calculation(pz_codes=[pz_code])

    n_diagnoses_this_year = calculate_kpis.calculate_kpi_2_total_new_diagnoses()

    context = {
        "number": n_diagnoses_this_year.total_eligible,
        "units": "patients",
        "description": "New diagnoses this audit year",
    }

    return render(
        request,
        "dashboard/components/cards/card_partials/secondary_card_partial.html",
        context,
    )


@login_and_otp_required()
def get_new_admissions_partial(request):
    """HTMX view that returns the number of new admissions for the current month"""

    # Get new admissions this month

    pz_code = request.session.get("pz_code")

    calculation_date = AuditPeriod.objects.get_audit_period_for_request(request).kpi_calculation_date()

    calculate_kpis = CalculateKPIS(
        calculation_date=calculation_date, return_pt_querysets=False
    )

    calculate_kpis.set_patients_for_calculation(pz_codes=[pz_code])

    n_admissions_this_month = (
        calculate_kpis.calculate_kpi_46_number_of_admissions().total_passed
    )

    context = {"number": n_admissions_this_month, "units": "children"}

    return render(
        request,
        "dashboard/components/cards/card_partials/secondary_card_partial.html",
        context,
    )


@login_and_otp_required()
def get_transitioned_to_adult_service_partial(request):
    """HTMX view that returns the number of patients who have been transitioned to the adult service"""

    pz_code = request.session.get("pz_code")

    calculation_date = AuditPeriod.objects.get_audit_period_for_request(request).kpi_calculation_date()

    calculate_kpis = CalculateKPIS(
        calculation_date=calculation_date, return_pt_querysets=True
    )

    calculate_kpis.set_patients_for_calculation(pz_codes=[pz_code])

    n_transitioned_to_adult_service = (
        calculate_kpis.calculate_total_service_transitions_to_adults().total_eligible  # this will return None if there are no eligible patients
    )

    context = {
        "number": n_transitioned_to_adult_service,
        "units": "children",
        "description": "Number of children transitioned to adult services this audit year",
    }

    return render(
        request,
        "dashboard/components/cards/card_partials/secondary_card_partial.html",
        context,
    )


@login_and_otp_required()
def get_moved_out_of_area_partial(request):
    """HTMX view that returns the number of patients who have been moved out of area"""

    pz_code = request.session.get("pz_code")

    calculation_date = AuditPeriod.objects.get_audit_period_for_request(request).kpi_calculation_date()

    calculate_kpis = CalculateKPIS(
        calculation_date=calculation_date, return_pt_querysets=True
    )

    calculate_kpis.set_patients_for_calculation(pz_codes=[pz_code])

    n_moved_out_of_area = (
        calculate_kpis.get_number_of_moved_out_of_area_this_audit_year()
    )

    context = {"number": n_moved_out_of_area, "units": "children"}

    return render(
        request,
        "dashboard/components/cards/card_partials/secondary_card_partial.html",
        context,
    )


@login_and_otp_required()
def get_n_on_hcl_partial(request):
    """HTMX view that returns the number of patients who are on HCL"""

    pz_code = request.session.get("pz_code")

    calculation_date = AuditPeriod.objects.get_audit_period_for_request(request).kpi_calculation_date()

    calculate_kpis = CalculateKPIS(
        calculation_date=calculation_date, return_pt_querysets=True
    )

    calculate_kpis.set_patients_for_calculation(pz_codes=[pz_code])

    hcl_use_kpi_result = calculate_kpis.calculate_kpi_24_hybrid_closed_loop_system()

    pct_hcl_use = (
        round(
            hcl_use_kpi_result.total_passed / hcl_use_kpi_result.total_eligible * 100, 1
        )
        if hcl_use_kpi_result.total_eligible is not None
        and hcl_use_kpi_result.total_eligible > 0
        else 0
    )

    context = {
        "numerator": hcl_use_kpi_result.total_passed,
        "denominator": hcl_use_kpi_result.total_eligible,
        "units": f"({pct_hcl_use}%)",
        "description": "Number of children using a hybrid closed loop system as a percentage of all children with type 1 diabetes",
    }

    return render(
        request,
        "dashboard/components/cards/card_partials/secondary_card_partial.html",
        context,
    )


@login_and_otp_required()
def get_pump_partial(request):
    """HTMX view that returns the number of patients who are on pump"""

    pz_code = request.session.get("pz_code")

    calculation_date = AuditPeriod.objects.get_audit_period_for_request(request).kpi_calculation_date()

    calculate_kpis = CalculateKPIS(
        calculation_date=calculation_date, return_pt_querysets=True
    )

    calculate_kpis.set_patients_for_calculation(pz_codes=[pz_code])

    pump_kpi_result = calculate_kpis.calculate_kpi_15_insulin_pump()

    pct_pump = (
        round(pump_kpi_result.total_passed / pump_kpi_result.total_eligible * 100, 1)
        if pump_kpi_result.total_eligible > 0
        else 0
    )

    context = {
        "numerator": pump_kpi_result.total_passed,
        "denominator": pump_kpi_result.total_eligible,
        "units": f"({pct_pump}%)",
        "description": "Number of children using an insulin pump as a percentage of all children with type 1 diabetes",
    }

    return render(
        request,
        "dashboard/components/cards/card_partials/secondary_card_partial.html",
        context,
    )


@login_and_otp_required()
def get_cgm_partial(request):
    """HTMX view that returns the number of patients who are on CGM"""

    pz_code = request.session.get("pz_code")

    calculation_date = AuditPeriod.objects.get_audit_period_for_request(request).kpi_calculation_date()

    calculate_kpis = CalculateKPIS(
        calculation_date=calculation_date, return_pt_querysets=True
    )

    calculate_kpis.set_patients_for_calculation(pz_codes=[pz_code])

    cgm_kpi_result = calculate_kpis.calculate_kpi_22_real_time_cgm_with_alarms()

    pct_cgm = (
        round(cgm_kpi_result.total_passed / cgm_kpi_result.total_eligible * 100, 1)
        if cgm_kpi_result.total_eligible > 0
        else 0
    )

    context = {
        "numerator": cgm_kpi_result.total_passed,
        "denominator": cgm_kpi_result.total_eligible,
        "units": f"({pct_cgm}%)",
    }

    return render(
        request,
        "dashboard/components/cards/card_partials/secondary_card_partial.html",
        context,
    )


def get_selected_chart_data(selected_chart: str, calculation_date: date, pz_code: str):
    """Return the data for the selected chart"""

    kpis = CalculateKPIS(calculation_date=calculation_date, return_pt_querysets=False)
    kpis.set_patients_for_calculation(pz_codes=[pz_code])

    if selected_chart == "new_diagnoses":
        return (
            kpis.calculate_kpi_2_total_new_diagnoses_stratified_by_quarter(),
            "All new diabetes diagnoses by quarter",
            "Numbers of patients newly diagnosed with any type of diabetes each quarter. These numbers include new diagnoses by quarter in blue. Cumulative totals by quarter are shown in grey.",
        )
    elif selected_chart == "new_admissions":
        return (
            kpis.calculate_kpi_46_number_of_admissions_stratified_by_quarter(),
            "All new diabetes admissions by quarter",
            "Numbers of patients with diabetes admitted to hospital for any reason by quarter. These numbers include all admissions by quarter in blue. Cumulative totals by quarter are shown in grey.",
        )
    elif selected_chart == "transitioned_to_adult_service":
        return (
            kpis.calculate_total_service_transitions_to_adults_stratified_by_quarter(),
            "All children transitioned to adult service by quarter",
            "Numbers of patients with diabetes transitioned to adult services by quarter. These numbers include all patients who transition to adults by quarter in blue. Cumulative totals by quarter are shown in grey.",
        )

