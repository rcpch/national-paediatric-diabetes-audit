import logging
from collections import defaultdict
from decimal import Decimal
from typing import Literal

from dateutil.relativedelta import relativedelta

# Django imports
from django.db.models import (
    Case,
    Count,
    Exists,
    F,
    IntegerField,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    Sum,
    When,
    DecimalField,
    ExpressionWrapper,
    DateField,
)
from datetime import date, timedelta
from project.npda.models.db_functions import Round
from project.constants.hba1c_format import HBA1C_FORMATS
from project.npda.kpi_class.kpis import CalculateKPIS
from project.npda.views.patient_report import template_data

# LOGGING
logger = logging.getLogger(__name__)


def get_pt_level_table_data(
    category: Literal[
        "health_checks",
        "additional_care_processes",
        "care_at_diagnosis",
        "outcomes",
        "treatment",
    ],
    calculate_kpis_object: CalculateKPIS,
    kpi_calculations_object: dict,
) -> tuple[list[str], list[dict]]:
    """Get data for pt level table

    - headers
    - row_data

    NOTE: kpi_30_retinal_screening is not included in the totals

    where row_data is a list of dicts with the following example structure (keys are pt.pk):
        {
                11: {
                    nhs_number: str,
                    kpi_25_hba1c: bool,
                    kpi_26_bmi: bool,
                    kpi_27_thyroid: bool,
                    kpi_28_blood_pressure: bool | None,
                    kpi_29_urinary_albumin: bool | None,
                    kpi_30_retinal_screening: bool | None,
                    kpi_31_foot_examination: bool | None,
                    total: list[int, int],
                },
                12: {
                    nhs_number: str,
                    kpi_25_hba1c: bool,
                    kpi_26_bmi: bool,
                    kpi_27_thyroid: bool,
                    kpi_28_blood_pressure: bool | None,
                    kpi_29_urinary_albumin: bool | None,
                    kpi_30_retinal_screening: bool | None,
                    kpi_31_foot_examination: bool | None,
                    total: list[int, int],
                },
                ...
            }
    """

    get_attribute_name = calculate_kpis_object.kpi_name_registry.get_attribute_name
    kpi_attr_names = [
        get_attribute_name(i) for i in template_data.KPI_CATEGORY_ATTR_MAP[category]
    ]

    if category == "health_checks":
        data = {}
        all_t1dm_pts = (
            calculate_kpis_object.calculate_kpi_3_total_t1dm().patient_querysets[
                "eligible"
            ]
        )
        all_t1dm_pts_with_complete_year_of_care = calculate_kpis_object.calculate_kpi_5_total_t1dm_complete_year().patient_querysets[
            "eligible"
        ]
        # First initialise the dict with all T1DM (kpi3)
        for pt in all_t1dm_pts:
            # Set all to None initially as updating as [True | False] if pt in [passed | failed]
            # querysets for each kpi -> if not in either, must mean they are ineligible (therefore None)
            data[pt.pk] = {kpi_attr_name: None for kpi_attr_name in kpi_attr_names}
            # Additional values we can calculate now
            data[pt.pk]["nhs_number"] = (
                pt.nhs_number or pt.unique_reference_number or "Unknown"
            )
            pt_is_gte_12yo = (
                pt.date_of_birth
                <= calculate_kpis_object.audit_start_date - relativedelta(years=12)
            )
            data[pt.pk]["is_gte_12yo"] = pt_is_gte_12yo
            # total = (passed / total)
            data[pt.pk]["total"] = [0, 6 if pt_is_gte_12yo else 3]

            # mark if complete year of care
            data[pt.pk]["is_complete_year_of_care"] = (
                pt in all_t1dm_pts_with_complete_year_of_care
            )

        # For each kpi, update the data dict with the pts that have passed and failed
        for kpi_attr_name in kpi_attr_names:
            kpi_pt_querysets = kpi_calculations_object["calculated_kpi_values"][
                kpi_attr_name
            ]["patient_querysets"]

            for pt in kpi_pt_querysets["passed"]:
                # Mark as completed
                data[pt.pk][kpi_attr_name] = True

                # Skip retinal screening as it's not included in the totals
                if kpi_attr_name == "kpi_30_retinal_screening":
                    continue

                # Increment the passed count otherwise
                data[pt.pk]["total"][0] += 1

            for pt in kpi_pt_querysets["failed"]:
                # Mark as failed
                data[pt.pk][kpi_attr_name] = False

        # Finally add the headers. Need to add nhs_number, is_gte_12yo, and total to the headers

        headers = (
            ["nhs_number", "is_gte_12yo"]
            # Put retinal screening at the end
            + [
                kpi_attr_name
                for kpi_attr_name in kpi_attr_names
                if kpi_attr_name != "kpi_30_retinal_screening"
            ]
            + ["total", "kpi_30_retinal_screening"]
        )
        return headers, data

    elif category == "additional_care_processes":
        data = {}

        # all t1dm pts
        all_t1dm_pts = (
            calculate_kpis_object.calculate_kpi_3_total_t1dm().patient_querysets[
                "eligible"
            ]
        )
        all_t1dm_pts_with_complete_year_of_care = calculate_kpis_object.calculate_kpi_5_total_t1dm_complete_year().patient_querysets[
            "eligible"
        ]
        for pt in all_t1dm_pts:
            # Set all to None initially as updating as [True | False] if pt in [passed | failed]
            # querysets for each kpi -> if not in either, must mean they are ineligible (therefore None)
            data[pt.pk] = {kpi_attr_name: None for kpi_attr_name in kpi_attr_names}
            # Additional values we can calculate now
            data[pt.pk]["nhs_number"] = (
                pt.nhs_number or pt.unique_reference_number or "Unknown"
            )
            # complete year of care
            data[pt.pk]["is_complete_year_of_care"] = (
                pt in all_t1dm_pts_with_complete_year_of_care
            )

        for kpi_attr_name in kpi_attr_names:
            # For each kpi, update the data dict with the pts that have passed and failed
            kpi_pt_querysets_passed = kpi_calculations_object["calculated_kpi_values"][
                kpi_attr_name
            ]["patient_querysets"]

            for pt in all_t1dm_pts:
                data[pt.pk][kpi_attr_name] = pt in kpi_pt_querysets_passed["passed"]

        # Finally add the headers. Need to add nhs_number

        headers = ["nhs_number"] + kpi_attr_names
        return headers, data

    elif category == "care_at_diagnosis":
        data = {}

        # all t1dm pts
        today = date.today()
        all_t1dm_pts = (
            calculate_kpis_object.calculate_kpi_3_total_t1dm()
            .patient_querysets["eligible"]
            .filter(
                # Additional filter for only those diagnosed within 90 days of today
                Q(diagnosis_date__gte=today - timedelta(days=90))
            )
        )

        all_t1dm_pts_with_complete_year_of_care = calculate_kpis_object.calculate_kpi_5_total_t1dm_complete_year().patient_querysets[
            "eligible"
        ].filter(
                # Additional filter for only those diagnosed within 90 days of today
                Q(diagnosis_date__gte=today - timedelta(days=90))
            )
        for pt in all_t1dm_pts:
            # Set all to None initially as updating as [True | False] if pt in [passed | failed]
            # querysets for each kpi -> if not in either, must mean they are ineligible (therefore None)
            data[pt.pk] = {kpi_attr_name: None for kpi_attr_name in kpi_attr_names}
            # Additional values we can calculate now
            data[pt.pk]["nhs_number"] = (
                pt.nhs_number or pt.unique_reference_number or "Unknown"
            )
            # complete year of care
            data[pt.pk]["is_complete_year_of_care"] = (
                pt in all_t1dm_pts_with_complete_year_of_care
            )

        for kpi_attr_name in kpi_attr_names:
            kpi_pt_querysets = kpi_calculations_object["calculated_kpi_values"][
                kpi_attr_name
            ]["patient_querysets"]

            for pt in kpi_pt_querysets["passed"].filter(
                # Additional filter for only those diagnosed within 90 days of today
                Q(diagnosis_date__gte=today - timedelta(days=90))
            ):
                data[pt.pk][kpi_attr_name] = True
                data[pt.pk]["nhs_number"] = (
                    pt.nhs_number or pt.unique_reference_number or "Unknown"
                )

            for pt in kpi_pt_querysets["failed"].filter(
                # Additional filter for only those diagnosed within 90 days of today
                Q(diagnosis_date__gte=today - timedelta(days=90))
            ):
                data[pt.pk][kpi_attr_name] = False
                data[pt.pk]["nhs_number"] = (
                    pt.nhs_number or pt.unique_reference_number or "Unknown"
                )

        # Finally add the headers. Need to add nhs_number
        headers = ["nhs_number"] + kpi_attr_names

        return headers, data

    elif category == "outcomes":
        # Need to do some manual work as calculate_kpi methods perform aggregations of individual
        # pt values.

        # Get the base eligible pts (all T1DM)
        all_t1dm_pts = (
            calculate_kpis_object.calculate_kpi_3_total_t1dm().patient_querysets[
                "eligible"
            ]
        )
        all_t1dm_pts_with_complete_year_of_care = calculate_kpis_object.calculate_kpi_5_total_t1dm_complete_year().patient_querysets[
            "eligible"
        ]
        pks_of_t1dm_pts_with_complete_year_of_care = set(
            all_t1dm_pts_with_complete_year_of_care.values_list("pk", flat=True)
        )

        data = defaultdict(dict)
        for pt in all_t1dm_pts:
            data[pt.pk]["nhs_number"] = (
                pt.nhs_number or pt.unique_reference_number or "Unknown"
            )

        # Start with the median hba1c values
        valid_visits_with_hba1c_values = (
            calculate_kpis_object._get_valid_visits_for_kpi_44_and_45(all_t1dm_pts)
            .annotate(
                # convert HbA1c % to mmol/mol when necessary
                hba1c_mmol_mol=Case(
                    When(
                        Q(hba1c_format=HBA1C_FORMATS[0][0]),
                        then=F("hba1c"),
                    ),
                    When(
                        Q(hba1c_format=HBA1C_FORMATS[1][0]),
                        then=(F("hba1c") - Round(Decimal("2.152")))
                        / Decimal("0.09148"),
                    ),
                    default=None,
                    output_field=DecimalField(
                        max_digits=5,
                        decimal_places=2,
                    ),
                )
            )
            .values(
                "hba1c_mmol_mol",
                "patient__pk",
                "patient__nhs_number",
                "patient__unique_reference_number",
            )
            .filter(hba1c_mmol_mol__isnull=False)
        )

        # Group HbA1c values by patient ID into a list so can use
        # calculate_median method
        # We're doing this in Python instead of Django ORM because median
        # aggregation gets complicated
        hba1c_values_by_patient = defaultdict(list)
        for visit in valid_visits_with_hba1c_values:
            hba1c_values_by_patient[visit["patient__pk"]].append(
                visit["hba1c_mmol_mol"]
            )

        for pt_pk in hba1c_values_by_patient:
            hba1c_values = hba1c_values_by_patient[pt_pk]
            # Calculate this patient's mean & median hba1c value in mmol/mol
            mean_hba1c_mmol_mol = calculate_kpis_object.calculate_mean(hba1c_values)
            median_hba1c_mmol_mol = calculate_kpis_object.calculate_median(hba1c_values)

            data[pt_pk]["kpi_44_mean_hba1c"] = round(mean_hba1c_mmol_mol)
            data[pt_pk]["kpi_45_median_hba1c"] = round(median_hba1c_mmol_mol)

            # convert to %
            data[pt_pk]["mean_hba1c_pct"] = round(
                (0.09148 * mean_hba1c_mmol_mol) + 2.152
                if mean_hba1c_mmol_mol > 0 and mean_hba1c_mmol_mol is not None
                else None,
                1,
            )
            data[pt_pk]["median_hba1c_pct"] = round(
                (0.09148 * median_hba1c_mmol_mol) + 2.152
                if median_hba1c_mmol_mol > 0 and median_hba1c_mmol_mol is not None
                else None,
                1,
            )

            # Remaining kpis 46-49
            # Kpi 46
            data[pt_pk][get_attribute_name(46)] = (
                calculate_kpis_object.get_number_of_admissions_for_patient(
                    pt_pk=pt_pk,
                )
            )

            # kpi 47
            data[pt_pk][get_attribute_name(47)] = (
                calculate_kpis_object.get_number_of_dka_admissions_for_patient(
                    pt_pk=pt_pk,
                )
            )

            # complete year of care
            data[pt_pk]["is_complete_year_of_care"] = (
                pt_pk in pks_of_t1dm_pts_with_complete_year_of_care
            )

        # Finally add the headers. Need to add nhs_number
        headers = ["nhs_number"] + kpi_attr_names

        # Convert defaultdict to dict
        data = dict(data)

        return headers, data

    elif category == "treatment":
        data = defaultdict(dict)

        # Maps for frontend rendering
        # Tx map
        tx_attr_vals_map = {
            get_attribute_name(13): "1-3 injections/day",
            get_attribute_name(14): "4+ injections/day",
            get_attribute_name(15): "Insulin pump",
            get_attribute_name(16): "1-3 injections + blood glucose lowering meds",
            get_attribute_name(17): "4+ injections + blood glucose lowering meds",
            get_attribute_name(18): "Insulin pump + blood glucose lowering meds",
            get_attribute_name(19): "Dietary management alone",
            get_attribute_name(20): "Dietary management + blood glucose lowering meds",
        }
        # CGM map
        cgm_attr_vals_map = {
            get_attribute_name(21): "Flash glucose monitor",
            get_attribute_name(22): "Continuous glucose monitor with alarms",
        }

        # all t1dm pts
        all_t1dm_pts = (
            calculate_kpis_object.calculate_kpi_3_total_t1dm().patient_querysets[
                "eligible"
            ]
        )
        all_t1dm_pts_with_complete_year_of_care = calculate_kpis_object.calculate_kpi_5_total_t1dm_complete_year().patient_querysets[
            "eligible"
        ]

        # Start constructing the data dict

        for pt in all_t1dm_pts:
            # Add nhs number
            data[pt.pk]["nhs_number"] = (
                pt.nhs_number or pt.unique_reference_number or "Unknown"
            )

            # Tx regimen col -> find the first True value in the tx_vals_attr_map
            data[pt.pk]["tx_regimen"] = None
            for tx_val_attr in tx_attr_vals_map:
                if (
                    kpi_calculations_object["calculated_kpi_values"][tx_val_attr][
                        "patient_querysets"
                    ]["passed"]
                    .filter(pk=pt.pk)
                    .exists()
                ):
                    data[pt.pk]["tx_regimen"] = tx_attr_vals_map[tx_val_attr]
                    break

            # CGM col -> find the first True value in the CGM kpis
            data[pt.pk]["cgm"] = None
            for glucose_monitoring_kpi_attr in cgm_attr_vals_map:
                if (
                    kpi_calculations_object["calculated_kpi_values"][
                        glucose_monitoring_kpi_attr
                    ]["patient_querysets"]["passed"]
                    .filter(pk=pt.pk)
                    .exists()
                ):
                    data[pt.pk]["cgm"] = cgm_attr_vals_map[glucose_monitoring_kpi_attr]
                    break

            # HCL col -> true or false
            data[pt.pk][get_attribute_name(24)] = (
                "Yes"
                if (
                    kpi_calculations_object["calculated_kpi_values"][
                        get_attribute_name(24)
                    ]["patient_querysets"]["passed"]
                    .filter(pk=pt.pk)
                    .exists()
                )
                else "No"
            )

            # complete year of care
            data[pt.pk]["is_complete_year_of_care"] = (
                pt in all_t1dm_pts_with_complete_year_of_care
            )

        # Finally add the headers. Need to add nhs_number
        headers = ["nhs_number", "tx_regimen", "cgm", get_attribute_name(24)]

        return headers, dict(data)

    raise NotImplementedError(f"Category {category} not yet implemented")
