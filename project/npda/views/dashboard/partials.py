import json
import logging

# Django imports
from django.http import HttpResponseBadRequest

# Django imports
from django.shortcuts import render

import project.constants.colors as colors
from project.constants.leave_pdu_reasons import LEAVE_PDU_REASONS
from project.npda.general_functions.map import (
    generate_dataframe_and_aggregated_distance_data_from_cases,
    get_children_by_pdu_audit_year,
)
from project.npda.general_functions.patient_report.queries import (
    count_admissions,
    count_admissions_by_quarter,
    count_cgm_use,
    count_hcl_use,
    count_new_diagnoses_by_quarter,
    count_pump_use,
    count_service_transitions_by_quarter,
)
from project.npda.general_functions.rcpch_nhs_organisations import (
    fetch_organisation_by_ods_code,
)
from project.npda.models.submission import Submission
from project.npda.views.decorators import check_data_permissions, login_and_otp_required
from project.settings import RCPCH_DEPRIVATION_TILES_URL

logger = logging.getLogger(__name__)

DEFAULT_CHART_HTML_HEIGHT = "18rem"


def _english_imd_year_for_audit_period(audit_period) -> int:
    """Map NPDA dataset year to England IMD publication year."""
    return 2025 if audit_period.get_dataset_year() >= 2026 else 2019


def _map_initial_era_for_audit_period(audit_period) -> str:
    """
    Map library era semantics:
    - 2021 era => England 2025 IMD (2021 boundaries)
    - 2011 era => England 2019 IMD (2011 boundaries)
    """
    return (
        "2021" if _english_imd_year_for_audit_period(audit_period) == 2025 else "2011"
    )


def _map_initial_nation_for_organisation(organisation: dict) -> str:
    """Derive map nation from organisation country when available."""
    country_raw = (
        organisation.get("country")
        or organisation.get("nation")
        or organisation.get("country_name")
        or ""
    )

    country = str(country_raw).strip().lower()
    if country == "england":
        return "england"
    if country == "wales":
        return "wales"
    if country == "scotland":
        return "scotland"
    if country in {"northern ireland", "northern_ireland"}:
        return "northern_ireland"

    return "all"


@login_and_otp_required()
@check_data_permissions()
def get_map_chart_partial(request, audit_period, pdu):

    if not request.htmx:
        return HttpResponseBadRequest("This view is only accessible via HTMX")

    submission = Submission.objects.get_submission_for_request(pdu, audit_period)

    if not submission:
        return render(
            request,
            "dashboard/map_chart_partial.html",
            {"info": "No patient data yet"},
        )

    lead_organisation_ods_code = (
        submission.paediatric_diabetes_unit.lead_organisation_ods_code
    )

    pdu_lead_organisation = fetch_organisation_by_ods_code(
        ods_code=lead_organisation_ods_code
    )

    try:
        # these are all registered patients for the current cohort at the selected organisation to be plotted in the map
        patients_to_plot = get_children_by_pdu_audit_year(
            submission, pdu_lead_organisation
        )

        # aggregated distances (mean, median, max, min) that patients have travelled to the selected organisation
        aggregated_distances, patient_distances_dataframe = (
            generate_dataframe_and_aggregated_distance_data_from_cases(
                filtered_cases=patients_to_plot
            )
        )

        map_patients = []
        if not patient_distances_dataframe.empty:
            for patient in patient_distances_dataframe.to_dict("records"):
                map_patients.append(
                    {
                        "id": patient["pk"],
                        "nhs_number": patient["nhs_number"]
                        if patient["nhs_number"]
                        else "N/A",
                        "unique_reference_number": patient["unique_reference_number"]
                        if patient["unique_reference_number"]
                        else "N/A",
                        "lat": patient["latitude"],
                        "lon": patient["longitude"],
                        "distance_km": f"{patient['distance_km']:.2f}",
                        "distance_mi": f"{patient['distance_mi']:.2f}",
                    }
                )

        return render(
            request,
            template_name="dashboard/map_chart_partial.html",
            context={
                "RCPCH_DEPRIVATION_TILES_URL": RCPCH_DEPRIVATION_TILES_URL,
                "aggregated_distances": aggregated_distances,
                "map_payload": {
                    "initialEra": _map_initial_era_for_audit_period(audit_period),
                    "initialNation": _map_initial_nation_for_organisation(
                        pdu_lead_organisation
                    ),
                    "patients": map_patients,
                    "leadCentre": {
                        "label": pdu.lead_organisation_name,
                        "lat": pdu.lead_organisation_geocoordinates.y,
                        "lon": pdu.lead_organisation_geocoordinates.x,
                    },
                },
            },
        )

    except Exception:
        logger.error("Error generating map chart", exc_info=True)
        return render(
            request,
            "dashboard/map_chart_partial.html",
            {"error": "Something went wrong!"},
        )


@login_and_otp_required()
@check_data_permissions()
def get_metric_scatter_plot(request, audit_period, pdu):
    """HTMX view that accepts a GET request with an object of waffle labels and percentages,
    returning a waffle chart rendered.

    Must have request.GET data -> template responsible for handling empty data"""

    try:
        if not request.htmx:
            return HttpResponseBadRequest("This view is only accessible via HTMX")

        if request.method == "POST":
            selected_chart = request.POST["scatter_plot_select"]
            data, title, tooltip_text = get_selected_chart_data(
                selected_chart, pdu, audit_period
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
        [data[q]["pct"] for q in data]
        passed = [data[q]["total_passed"] for q in data]
        cumulative_sum = 0
        incremental_passed = [
            (cumulative_sum := cumulative_sum + data[q]["total_passed"]) for q in data
        ]
        [data[q]["total_eligible"] for q in data]
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
                marker={
                    "color": colors.RCPCH_LIGHT_GREY,  # Change to desired color
                    "line": {
                        "color": colors.RCPCH_LIGHT_GREY,
                        "width": 1,
                    },  # Add border
                    "symbol": "square",
                    "size": 12,
                },
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
                marker={
                    "size": 12,
                    "color": all_colors,
                    "symbol": "square",
                },
                line={"color": colors.RCPCH_LIGHT_BLUE},
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
            font={"color": colors.RCPCH_PINK, "size": 12},
            yshift=yshift,
        )

        # Layout adjustments
        fig.update_layout(
            xaxis={"title": "Quarter", "range": [-0.5, len(quarters) - 0.5]},
            yaxis={"title": "Number of children"},
            showlegend=True,
            template="simple_white",  # Clean grid style
            margin={"l": 0, "r": 0, "t": 0, "b": 0},
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
    except Exception:
        logger.error("Error generating metric scatter plot", exc_info=True)
        return render(
            request,
            "dashboard/metric_scatter_plot_partial.html",
            {"error": "Something went wrong!"},
        )


@login_and_otp_required()
@check_data_permissions()
def get_new_diagnoses_partial(request, audit_period, pdu):
    """HTMX view that returns the number of new diagnoses for the current submission"""

    sub = Submission.objects.get_submission_for_request(pdu, audit_period)

    if sub:
        count = sub.patients.filter(diagnosis_date__gte=audit_period.start_date).count()
    else:
        count = 0

    context = {
        "number": count,
        "units": "patients",
        "description": "New diagnoses this audit year",
    }

    return render(
        request,
        "dashboard/components/cards/card_partials/secondary_card_partial.html",
        context,
    )


@login_and_otp_required()
@check_data_permissions()
def get_new_admissions_partial(request, audit_period, pdu):
    """HTMX view that returns the number of new admissions for the current audit period"""

    n_admissions = count_admissions(pdu, audit_period)

    context = {"number": n_admissions, "units": "children"}

    return render(
        request,
        "dashboard/components/cards/card_partials/secondary_card_partial.html",
        context,
    )


@login_and_otp_required()
@check_data_permissions()
def get_transitioned_to_adult_service_partial(request, audit_period, pdu):
    """HTMX view that returns the number of patients who have been transitioned to the adult service"""

    sub = Submission.objects.get_submission_for_request(pdu, audit_period)

    if sub:
        count = sub.patients.filter(
            paediatric_diabetes_units__reason_leaving_service=LEAVE_PDU_REASONS[0][0]
        ).count()
    else:
        count = 0

    context = {
        "number": count,
        "units": "children",
        "description": "Number of children transitioned to adult services this audit year",
    }

    return render(
        request,
        "dashboard/components/cards/card_partials/secondary_card_partial.html",
        context,
    )


@login_and_otp_required()
@check_data_permissions()
def get_moved_out_of_area_partial(request, audit_period, pdu):
    """HTMX view that returns the number of patients who have been moved out of area"""

    sub = Submission.objects.get_submission_for_request(pdu, audit_period)

    if sub:
        count = sub.patients.filter(
            paediatric_diabetes_units__reason_leaving_service=LEAVE_PDU_REASONS[1][0]
        ).count()
    else:
        count = 0

    context = {"number": count, "units": "children"}

    return render(
        request,
        "dashboard/components/cards/card_partials/secondary_card_partial.html",
        context,
    )


@login_and_otp_required()
@check_data_permissions()
def get_n_on_hcl_partial(request, audit_period, pdu):
    """HTMX view that returns the number of patients who are on HCL"""

    passed, eligible = count_hcl_use(pdu, audit_period)

    pct_hcl_use = round(passed / eligible * 100, 1) if eligible and eligible > 0 else 0

    context = {
        "numerator": passed,
        "denominator": eligible,
        "units": f"({pct_hcl_use}%)",
        "description": "Number of children using a hybrid closed loop system as a percentage of all children with type 1 diabetes",
    }

    return render(
        request,
        "dashboard/components/cards/card_partials/secondary_card_partial.html",
        context,
    )


@login_and_otp_required()
@check_data_permissions()
def get_pump_partial(request, audit_period, pdu):
    """HTMX view that returns the number of patients who are on pump"""

    passed, eligible = count_pump_use(pdu, audit_period)

    pct_pump = round(passed / eligible * 100, 1) if eligible > 0 else 0

    context = {
        "numerator": passed,
        "denominator": eligible,
        "units": f"({pct_pump}%)",
        "description": "Number of children using an insulin pump as a percentage of all children with type 1 diabetes",
    }

    return render(
        request,
        "dashboard/components/cards/card_partials/secondary_card_partial.html",
        context,
    )


@login_and_otp_required()
@check_data_permissions()
def get_cgm_partial(request, audit_period, pdu):
    """HTMX view that returns the number of patients who are on CGM"""

    passed, eligible = count_cgm_use(pdu, audit_period)

    pct_cgm = round(passed / eligible * 100, 1) if eligible > 0 else 0

    context = {
        "numerator": passed,
        "denominator": eligible,
        "units": f"({pct_cgm}%)",
    }

    return render(
        request,
        "dashboard/components/cards/card_partials/secondary_card_partial.html",
        context,
    )


def get_selected_chart_data(selected_chart: str, pdu, audit_period):
    """Return the data for the selected chart"""

    if selected_chart == "new_diagnoses":
        return (
            count_new_diagnoses_by_quarter(pdu, audit_period),
            "All new diabetes diagnoses by quarter",
            "Numbers of patients newly diagnosed with any type of diabetes each quarter. These numbers include new diagnoses by quarter in blue. Cumulative totals by quarter are shown in grey.",
        )
    elif selected_chart == "new_admissions":
        return (
            count_admissions_by_quarter(pdu, audit_period),
            "All new diabetes admissions by quarter",
            "Numbers of patients with diabetes admitted to hospital for any reason by quarter. These numbers include all admissions by quarter in blue. Cumulative totals by quarter are shown in grey.",
        )
    elif selected_chart == "transitioned_to_adult_service":
        return (
            count_service_transitions_by_quarter(pdu, audit_period),
            "All children transitioned to adult service by quarter",
            "Numbers of patients with diabetes transitioned to adult services by quarter. These numbers include all patients who transition to adults by quarter in blue. Cumulative totals by quarter are shown in grey.",
        )
