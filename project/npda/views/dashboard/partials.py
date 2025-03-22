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
from project.npda.views.decorators import login_and_otp_required

logger = logging.getLogger(__name__)

DEFAULT_CHART_HTML_HEIGHT = "18rem"


@login_and_otp_required()
def get_map_chart_partial(request):

    if not request.htmx:
        return HttpResponseBadRequest("This view is only accessible via HTMX")

    # Fetch data from query parameters
    pz_code: str = request.session.get("pz_code")
    selected_audit_year = request.session.get("selected_audit_year")

    try:
        paediatric_diabetes_unit = PaediatricDiabetesUnitClass.objects.get(
            pz_code=pz_code
        )

        # get lead organisation for the selected PDU
        pdu_lead_organisation = fetch_organisation_by_ods_code(
            ods_code=paediatric_diabetes_unit.lead_organisation_ods_code
        )
    except:
        raise ValueError(
            f"Lead organisation for PDU {paediatric_diabetes_unit.lead_organisation_ods_code=} not found"
        )

    try:

        # thes are all registered patients for the current cohort at the selected organisation to be plotted in the map
        patients_to_plot = get_children_by_pdu_audit_year(
            paediatric_diabetes_unit=paediatric_diabetes_unit,
            paediatric_diabetes_unit_lead_organisation=pdu_lead_organisation,
            audit_year=selected_audit_year,
        )

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
                paediatric_diabetes_unit=paediatric_diabetes_unit,
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
def get_hcl_scatter_plot(request):
    """HTMX view that accepts a GET request with an object of waffle labels and percentages,
    returning a waffle chart rendered.

    Must have request.GET data -> template responsible for handling empty data"""

    try:

        if not request.htmx:
            return HttpResponseBadRequest("This view is only accessible via HTMX")

        if not (request_data := request.GET.get("data", None)):
            return HttpResponseBadRequest("No data provided")

        # Fetch data from query parameters
        data = json.loads(request_data)

        # Extracting data
        quarters = [f"Q{q}" for q in data]
        percentages = [data[q]["pct"] for q in data]
        passed = [data[q]["total_passed"] for q in data]
        eligible = [data[q]["total_eligible"] for q in data]
        all_colors = [colors.RCPCH_LIGHT_BLUE for _ in data]
        # highlight the last quarter
        all_colors[-1] = colors.RCPCH_PINK

        # Create scatter plot
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=quarters,
                y=percentages,
                mode="lines+markers",
                marker=dict(
                    size=12,
                    color=all_colors,
                    symbol="square",
                ),
                line=dict(color=colors.RCPCH_LIGHT_BLUE),
                hovertemplate="<b>%{x}</b>:Eligible passed: %{customdata[0]} / %{customdata[1]} (%{y:.1f}%)<extra></extra>",
                customdata=list(zip(passed, eligible)),
            )
        )

        # Add annotation for last quarter
        last_pct = percentages[-1]
        # Offset below point if penultimate point higher than final point
        Y_SHIFT = 20
        if len(percentages) > 1 and percentages[-2] >= last_pct:
            # If the final point is < 10, don't offset below as goes off the chart
            yshift = -Y_SHIFT if last_pct > (Y_SHIFT) else Y_SHIFT
        else:
            # Don't need to account for going off the chart at top as added space
            yshift = Y_SHIFT
        fig.add_annotation(
            x=quarters[-1],
            y=percentages[-1],
            text=f"{percentages[-1]}%",
            showarrow=False,
            font=dict(color=colors.RCPCH_PINK, size=12),
            yshift=yshift,
        )

        # Layout adjustments
        fig.update_layout(
            xaxis=dict(title="Quarter", range=[-0.5, len(quarters) - 0.5]),
            yaxis=dict(title="% CYP", range=[0, 110]),
            showlegend=False,
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
            "dashboard/hcl_scatter_plot_partial.html",
            {"chart_html": chart_html},
        )
    except Exception as e:
        logger.error("Error generating hcl scatter plot", exc_info=True)
        return render(
            request,
            "dashboard/hcl_scatter_plot_partial.html",
            {"error": "Something went wrong!"},
        )


@login_and_otp_required()
def get_new_diagnoses_partial(request):
    """HTMX view that returns the number of new diagnoses for the current month"""

    # Get new diagnoses this month

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

    selected_audit_year = int(request.session.get("selected_audit_year"))

    if Submission.objects.filter(
        paediatric_diabetes_unit=pdu,
        audit_year=selected_audit_year,
        submission_active=True,
    ).exists():
        submission = Submission.objects.get(
            paediatric_diabetes_unit=pdu,
            audit_year=selected_audit_year,
            submission_active=True,
        )
    else:
        submission = None

    if selected_audit_year <= date.today().year:
        # The day after the audit year end date
        calculation_date = date(selected_audit_year, 4, 1)
    else:
        today = date.today()
        calculation_date = date(selected_audit_year, today.month, today.day)

    calculate_kpis = CalculateKPIS(
        calculation_date=calculation_date, return_pt_querysets=True
    )

    calculate_kpis.set_patients_for_calculation(pz_codes=[pz_code])

    # n_diagnoses_this_month = calculate_kpis.get_new_diagnoses_this_month()
    if submission:
        n_diagnoses_this_submission = calculate_kpis.get_new_diagnoses_this_submission(
            submission=submission
        )
    else:
        n_diagnoses_this_submission = 0

    context = {
        "number": n_diagnoses_this_submission,
        "units": "(patients)",
        "description": "New diagnoses this submission",
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

    selected_audit_year = int(request.session.get("selected_audit_year"))

    if selected_audit_year <= 2024:
        # The day after the audit year end date
        calculation_date = date(selected_audit_year, 4, 1)
    else:
        today = date.today()
        calculation_date = date(selected_audit_year, today.month, today.day)

    calculate_kpis = CalculateKPIS(
        calculation_date=calculation_date, return_pt_querysets=True
    )

    calculate_kpis.set_patients_for_calculation(pz_codes=[pz_code])

    n_admissions_this_month = calculate_kpis.get_number_of_admissions_this_month()

    context = {"number": n_admissions_this_month, "units": "(N / month)"}

    return render(
        request,
        "dashboard/components/cards/card_partials/secondary_card_partial.html",
        context,
    )


@login_and_otp_required()
def get_transitioned_to_adult_service_partial(request):
    """HTMX view that returns the number of patients who have been transitioned to the adult service"""

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

    selected_audit_year = int(request.session.get("selected_audit_year"))

    if selected_audit_year <= 2024:
        # The day after the audit year end date
        calculation_date = date(selected_audit_year, 4, 1)
    else:
        today = date.today()
        calculation_date = date(selected_audit_year, today.month, today.day)

    calculate_kpis = CalculateKPIS(
        calculation_date=calculation_date, return_pt_querysets=True
    )

    calculate_kpis.set_patients_for_calculation(pz_codes=[pz_code])

    n_transitioned_to_adult_service = (
        calculate_kpis.get_number_of_transitioned_to_adult_service_this_month()
    )

    context = {"number": n_transitioned_to_adult_service, "units": "(N / month)"}

    return render(
        request,
        "dashboard/components/cards/card_partials/secondary_card_partial.html",
        context,
    )


@login_and_otp_required()
def get_moved_out_of_area_partial(request):
    """HTMX view that returns the number of patients who have been moved out of area"""

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

    selected_audit_year = int(request.session.get("selected_audit_year"))

    if selected_audit_year <= 2024:
        # The day after the audit year end date
        calculation_date = date(selected_audit_year, 4, 1)
    else:
        today = date.today()
        calculation_date = date(selected_audit_year, today.month, today.day)

    calculate_kpis = CalculateKPIS(
        calculation_date=calculation_date, return_pt_querysets=True
    )

    calculate_kpis.set_patients_for_calculation(pz_codes=[pz_code])

    n_moved_out_of_area = calculate_kpis.get_number_of_moved_out_of_area_this_month()

    context = {"number": n_moved_out_of_area, "units": "(N / month)"}

    return render(
        request,
        "dashboard/components/cards/card_partials/secondary_card_partial.html",
        context,
    )


@login_and_otp_required()
def get_n_on_hcl_partial(request):
    """HTMX view that returns the number of patients who are on HCL"""

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

    selected_audit_year = int(request.session.get("selected_audit_year"))

    if selected_audit_year <= 2024:
        # The day after the audit year end date
        calculation_date = date(selected_audit_year, 4, 1)
    else:
        today = date.today()
        calculation_date = date(selected_audit_year, today.month, today.day)

    calculate_kpis = CalculateKPIS(
        calculation_date=calculation_date, return_pt_querysets=True
    )

    calculate_kpis.set_patients_for_calculation(pz_codes=[pz_code])

    hcl_use_kpi_result = calculate_kpis.calculate_kpi_24_hybrid_closed_loop_system()

    n_hcl_use = hcl_use_kpi_result.total_passed

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

    selected_audit_year = int(request.session.get("selected_audit_year"))

    if selected_audit_year <= 2024:
        # The day after the audit year end date
        calculation_date = date(selected_audit_year, 4, 1)
    else:
        today = date.today()
        calculation_date = date(selected_audit_year, today.month, today.day)

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

    selected_audit_year = int(request.session.get("selected_audit_year"))

    if selected_audit_year <= 2024:
        # The day after the audit year end date
        calculation_date = date(selected_audit_year, 4, 1)
    else:
        today = date.today()
        calculation_date = date(selected_audit_year, today.month, today.day)

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
