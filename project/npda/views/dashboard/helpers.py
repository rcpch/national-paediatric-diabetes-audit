"""Helper functions for dashboard views including calculations and data manipulation."""

# Python imports
import logging
from collections import Counter, defaultdict
from decimal import Decimal
from typing import Literal

from dateutil.relativedelta import relativedelta
from django.db.models import QuerySet

from project.constants.ethnicities import ETHNICITIES
from project.constants.sex_types import SEX_TYPE
from project.constants.types.kpi_types import KPIRegistry
from project.npda.kpi_class.kpis import CalculateKPIS
from project.npda.models.patient import Patient

# LOGGING
logger = logging.getLogger(__name__)


def add_number_of_figures_coloured_for_chart(
    value_counts_dict: dict[
        Literal["care", "died_or_transitioned", "comorbidity_and_testing"],
        dict[Literal["total_eligible", "total_ineligible", "pct"], int],
    ],
    n_figures_total: int = 5,
) -> dict[Literal["total_eligible", "total_ineligible", "pct", "figures_coloured"], int]:
    """
    Add number of figures coloured to a value counts dict
    """
    # divisor is 100 / n_figures_total
    divisor = 100 / n_figures_total

    for category, vcs in value_counts_dict.items():
        for key, value in vcs.items():
            value_counts_dict[category][key]["figures_coloured"] = int(value["pct"] / divisor)

    return dict(value_counts_dict)


def get_care_at_diagnosis_vcs_pct(
    kpi_41_values: dict,
    kpi_42_values: dict,
    kpi_43_values: dict,
) -> dict:
    """Get value counts for care at diagnosis KPIs (41, 42, 43)

    - coeliac (KPI41)
    - thyroid (KPI42)
    - carb counting ed (KPI43)

    NOTE: rounds DOWN (convert float to int) for percentage calculation
    """
    data = {}

    data["coeliac_disease_screening"] = {
        "count": kpi_41_values["total_passed"],
        "total": kpi_41_values["total_eligible"],
        "pct": (
            int(kpi_41_values["total_passed"] / kpi_41_values["total_eligible"] * 100)
            if kpi_41_values["total_eligible"]
            else 0
        ),
        "label": "Coeliac Disease Screening",
    }

    data["thyroid_disease_screening"] = {
        "count": kpi_42_values["total_passed"],
        "total": kpi_42_values["total_eligible"],
        "pct": (
            int(kpi_42_values["total_passed"] / kpi_42_values["total_eligible"] * 100)
            if kpi_42_values["total_eligible"]
            else 0
        ),
        "label": "Thyroid Disease Screening",
    }

    data["carbohydrate_counting_education"] = {
        "count": kpi_43_values["total_passed"],
        "total": kpi_43_values["total_eligible"],
        "pct": (
            int(kpi_43_values["total_passed"] / kpi_43_values["total_eligible"] * 100)
            if kpi_43_values["total_eligible"]
            else 0
        ),
        "label": "Carbohydrate Counting Education",
    }

    return data


def get_hc_completion_rate_vcs(
    kpi_32_2_values: dict,
    kpi_32_3_values: dict,
):
    """
    Get value counts for health checks completion rates
    """

    # Just need pass and fail
    vcs = {}

    kpi_32_2_passed = kpi_32_2_values["total_passed"]
    kpi_32_2_total = kpi_32_2_values["total_eligible"]
    kpi_32_3_passed = kpi_32_3_values["total_passed"]
    kpi_32_3_total = kpi_32_3_values["total_eligible"]

    # Overall
    # For overall, we need to sum total passed and total eligible for kpis 31_2 and 32_3.
    # We IGNORE 32_1 as this is a count of health checks, not patients!
    kpi_32_1_pct = (
        int((kpi_32_2_passed + kpi_32_3_passed) / (kpi_32_2_total + kpi_32_3_total) * 100)
        if kpi_32_2_total + kpi_32_3_total
        else 0
    )
    vcs["kpi_32_1_values"] = {
        "count": kpi_32_2_passed + kpi_32_3_passed,
        "total": kpi_32_2_total + kpi_32_3_total,
        "pct": kpi_32_1_pct,
        "label": "Overall",
    }

    # <12 years old
    vcs["kpi_32_2_values"] = {
        "count": kpi_32_2_passed,
        "total": kpi_32_2_total,
        "pct": int(kpi_32_2_passed / kpi_32_2_total * 100) if kpi_32_2_total else 0,
        "label": "<12 years old",
    }

    # >=12 years old
    vcs["kpi_32_3_values"] = {
        "count": kpi_32_3_passed,
        "total": kpi_32_3_total,
        "pct": int(kpi_32_3_passed / kpi_32_3_total * 100) if kpi_32_3_total else 0,
        "label": ">=12 years old",
    }

    return vcs


def get_hba1c_value_counts_stratified_by_diabetes_type(
    calculate_kpis_instance: CalculateKPIS,
) -> dict:
    """Gets the data for plotting on the chart.

    The KPI class does not stratify by diabetes type so we need to do this here."""

    # Get the query sets (the hba1c value)
    hba1c_vals = calculate_kpis_instance.calculate_kpi_hba1c_vals_stratified_by_diabetes_type()

    return hba1c_vals


def get_pt_characteristics_value_counts_pct(
    kpi_name_registry: KPIRegistry,
    kpi_calculations_object: dict,
) -> dict[
    Literal["care", "died_or_transitioned", "comorbidity_and_testing"],
    dict[Literal["total_eligible", "total_ineligible", "pct"], int],
]:
    """Gets value counts dict for:

    care
    - age_gte_12yo (KPI4)
    - complete_year_of_care (KPI5)
    - age_gte_12yo_and_complete_year_of_care (KPI6)

    died_or_transitioned
    - died (KPI8)
    - transitioned (KPI9)

    comorbidity_and_testing
    - coeliac (KPI10)
    - thyroid (kpi11)
    - ketone_testing (KPI12)

    NOTE: rounds DOWN (convert float to int) for percentage calculation
    """
    # Get attribute names and labels
    relevant_kpis = [4, 5, 6, 8, 9, 10, 11, 12]
    kpi_attr_names = [kpi_name_registry.get_attribute_name(kpi) for kpi in relevant_kpis]

    value_counts = defaultdict(lambda: {"count": 0, "total": 0, "pct": 0})
    # These are all just counts so only total_eligble and total_ineligible have values
    for kpi_attr in kpi_attr_names:

        total_eligible = kpi_calculations_object[kpi_attr]["total_eligible"]
        total_ineligible = kpi_calculations_object[kpi_attr]["total_ineligible"]

        # Need all 3 for front end chart
        value_counts[kpi_attr]["count"] = total_eligible
        value_counts[kpi_attr]["total"] = total_eligible + total_ineligible
        value_counts[kpi_attr]["pct"] = (
            int(total_eligible / value_counts[kpi_attr]["total"] * 100)
            if value_counts[kpi_attr]["total"] > 0
            else 0
        )

    # Now put into the 3 categories
    categories_vc = defaultdict(dict)
    for kpi in [4, 5, 6]:
        kpi_attr = kpi_name_registry.get_attribute_name(kpi)
        categories_vc["care"][kpi_attr] = value_counts[kpi_attr]

    for kpi in [8, 9]:
        kpi_attr = kpi_name_registry.get_attribute_name(kpi)
        categories_vc["died_or_transitioned"][kpi_attr] = value_counts[kpi_attr]

    for kpi in [10, 11, 12]:
        kpi_attr = kpi_name_registry.get_attribute_name(kpi)
        categories_vc["comorbidity_and_testing"][kpi_attr] = value_counts[kpi_attr]

    return dict(categories_vc)


def get_total_eligible_pts_diabetes_type_value_counts(
    eligible_pts_queryset: QuerySet,
) -> dict:
    """Gets value counts dict for total eligible patients stratified by diabetes type"""

    eligible_pts_diabetes_type_value_counts_raw = Counter(
        eligible_pts_queryset.values_list("diabetes_type", flat=True)
    )

    # Other types will be denoted as "Other rare forms"
    diabetes_type_label_map = {
        1: "T1DM",
        2: "T2DM",
    }

    # Convert to labels
    eligible_pts_diabetes_type_value_counts = defaultdict(int)
    for key, value in eligible_pts_diabetes_type_value_counts_raw.items():
        eligible_pts_diabetes_type_value_counts[
            diabetes_type_label_map.get(key, "Other rare forms")
        ] += value

    return eligible_pts_diabetes_type_value_counts


def get_tx_regimen_value_counts_pcts(
    kpi_name_registry: KPIRegistry,
    kpi_calculations_object: dict,
) -> dict:
    """Get value counts with pcts for treatment regimen KPIs

    - treatment_regimen (KPIs 13-15)
    """
    # Get attribute names and labels
    relevant_kpis = [13, 14, 15]
    # Labels used for bar chart htmx partial
    labels = [
        "1-3 insulin injections per day",
        "Multiple injections per day",
        "Insulin pump",
    ]
    kpi_attr_names = [kpi_name_registry.get_attribute_name(kpi) for kpi in relevant_kpis]

    value_counts = defaultdict(lambda: {"count": 0, "total": 0, "pct": 0})

    for label, kpi_attr in zip(labels, kpi_attr_names):

        count = kpi_calculations_object[kpi_attr]["total_passed"]
        total = kpi_calculations_object[kpi_attr]["total_eligible"]

        # Need these keys for bar chart partial
        value_counts[kpi_attr]["count"] = count
        value_counts[kpi_attr]["total"] = total
        value_counts[kpi_attr]["pct"] = int(count / total * 100) if total > 0 else 0
        value_counts[kpi_attr]["label"] = label

    return dict(value_counts)


def get_glucose_monitoring_value_counts_pcts(
    kpi_name_registry: KPIRegistry,
    kpi_calculations_object: dict,
) -> dict:
    """Get value counts with pcts for glucose monitoring KPIs:

    - glucose_monitoring (KPIs 21-23)
    """
    # Get attribute names and labels
    relevant_kpis = [21, 22, 23]
    kpi_attr_names = [kpi_name_registry.get_attribute_name(kpi) for kpi in relevant_kpis]

    # Labels used for bar chart htmx partial
    labels = [
        "Flash glucose monitor",
        "Continuous glucose monitor with alarms",
        "T1DM and Continuous glucose monitor with alarms",
    ]

    value_counts = defaultdict(lambda: {"count": 0, "total": 0, "pct": 0})

    for label, kpi_attr in zip(labels, kpi_attr_names):

        count = kpi_calculations_object[kpi_attr]["total_passed"]
        total = kpi_calculations_object[kpi_attr]["total_eligible"]

        # Need these keys for bar chart partial
        value_counts[kpi_attr]["count"] = count
        value_counts[kpi_attr]["total"] = total
        value_counts[kpi_attr]["pct"] = int(count / total * 100) if total > 0 else 0
        value_counts[kpi_attr]["label"] = label

    return dict(value_counts)


def get_additional_care_processes_value_counts(
    additional_care_processes_kpi_attr_names: list[str],
    kpi_calculations_object: dict,
) -> dict:
    """Denominator already is CYP with T1DM (with completed year of care)

    So can just use values from kpi calculator. Just need to restructure and calc pct"""

    labels = [
        "HbA1c 4+",
        "Psychological Assessment",
        "Smoking status screened",
        "Referral to smoking cessation service",
        "Additional dietetic appointment offered",
        "Patients attending additional dietetic appointment",
        "Influenza immunisation reccommended",
        "Sick day rules advice",
    ]

    value_counts = defaultdict(lambda: {"count": 0, "total": 0, "pct": 0})

    for ix, kpi_attr in enumerate(additional_care_processes_kpi_attr_names):
        total_eligible = kpi_calculations_object[kpi_attr]["total_eligible"]
        total_passed = kpi_calculations_object[kpi_attr]["total_passed"]

        # Need all 3 for front end chart
        value_counts[kpi_attr]["count"] = total_passed
        value_counts[kpi_attr]["total"] = total_eligible
        value_counts[kpi_attr]["pct"] = (
            round(total_passed / total_eligible * 100, 1) if total_eligible > 0 else 0
        )
        value_counts[kpi_attr]["label"] = labels[ix]

    return dict(value_counts)


def get_admissions_value_counts_absolute(
    admissions_kpi_attr_names: list[str],
    kpi_calculations_object=dict,
):
    """Can simply get the .total_passed value for the absolute counts"""

    absolute_value_counts = {}
    for kpi_attr in admissions_kpi_attr_names:
        absolute_value_counts[kpi_attr] = kpi_calculations_object[kpi_attr]["total_passed"]

    return absolute_value_counts


def get_pt_demographic_value_counts(
    all_eligible_pts_queryset: QuerySet[Patient],
) -> tuple[
    dict[Literal["Female", "Male", "Unknown"], int],
    dict[str, int],
    dict[
        Literal[
            1,
            2,
            3,
            4,
            5,
        ],
        int,
    ],
]:
    """Get value counts for pt demographics:

    - sex
    - ethnicity
    - imd
    """

    all_values = all_eligible_pts_queryset.values(
        "sex", "ethnicity", "index_of_multiple_deprivation_quintile"
    )
    sex_map = dict(SEX_TYPE)
    sex_counts = Counter(sex_map[item["sex"]] for item in all_values if item["sex"] in sex_map)
    ethnicity_map = dict(ETHNICITIES)
    ethnicity_counts = Counter(
        ethnicity_map[item["ethnicity"]]
        for item in all_values
        if item["ethnicity"] in ethnicity_map
    )
    imd_map = {
        1: "1st Quintile",
        2: "2nd Quintile",
        3: "3rd Quintile",
        4: "4th Quintile",
        5: "5th Quintile",
    }
    imd_counts = Counter(
        imd_map.get(item["index_of_multiple_deprivation_quintile"], "Unknown")
        for item in all_values
    )

    return (
        sex_counts,
        ethnicity_counts,
        imd_counts,
    )


def convert_value_counts_dict_to_pct(value_counts_dict: dict):
    """
    Convert a value counts dict to percentages
    """
    total = sum(value_counts_dict.values())

    value_counts_dict_pct = {}

    for key, value in value_counts_dict.items():
        pct = value / total * 100
        value_counts_dict_pct[key] = int(pct) if pct >= 1 else round(pct, 1)

    return value_counts_dict_pct


def get_list_of_shortened_ticktext_labels(
    x: list[str],
    cut_off_char_len=10,
) -> list[str]:
    """Takes in a list of labels and intelligently shortens,
    adding `...` if appropriate."""
    shortened_ticktext_labels = []
    for label in x:
        if len(label) > cut_off_char_len:
            # Don't want to cut off in middle of word so split on spaces,
            # and keep as many full words as possible until we reach the cut off
            shortened_label_parts = []
            current_len = 0
            label_split = label.split(" ")
            for word in label_split:
                shortened_label_parts.append(word)
                current_len += len(word)
                if current_len > cut_off_char_len:
                    break

            shortened_label = f"{' '.join(shortened_label_parts)}"
            if len(shortened_label_parts) < len(label_split):
                shortened_label += "..."
            shortened_ticktext_labels.append(shortened_label)
        else:
            shortened_ticktext_labels.append(label)
    return shortened_ticktext_labels
