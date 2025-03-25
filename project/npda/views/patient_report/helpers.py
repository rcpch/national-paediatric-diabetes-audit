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
    kpi_attr_names = [get_attribute_name(i) for i in template_data.KPI_CATEGORY_ATTR_MAP[category]]

    if category == "health_checks":

        data = {}
        # First initialise the dict with all pts -> for health checks, this is KPI5 which can be found
        # via kpi_25's eligible pts
        for pt in kpi_calculations_object["calculated_kpi_values"]["kpi_25_hba1c"][
            "patient_querysets"
        ]["eligible"]:
            # Set all to None initially as updating as [True | False] if pt in [passed | failed]
            # querysets for each kpi -> if not in either, must mean they are ineligible (therefore None)
            data[pt.pk] = {kpi_attr_name: None for kpi_attr_name in kpi_attr_names}
            # Additional values we can calculate now
            data[pt.pk]["nhs_number"] = pt.nhs_number or pt.unique_reference_number or "Unknown"
            pt_is_gte_12yo = (
                pt.date_of_birth <= calculate_kpis_object.audit_start_date - relativedelta(years=12)
            )
            data[pt.pk]["is_gte_12yo"] = pt_is_gte_12yo
            # total = (passed / total)
            data[pt.pk]["total"] = [0, 6 if pt_is_gte_12yo else 3]

        # For each kpi, update the data dict with the pts that have passed and failed
        for kpi_attr_name in kpi_attr_names:

            kpi_pt_querysets = kpi_calculations_object["calculated_kpi_values"][kpi_attr_name][
                "patient_querysets"
            ]

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
        # Initialise with all eligible pts' pks as the key. Use kpi40 eligible
        # as this is KPI1 (all eligible pts)
        kpi_40_attr_name = calculate_kpis_object.kpi_name_registry.get_attribute_name(40)
        for pt in kpi_calculations_object["calculated_kpi_values"][kpi_40_attr_name][
            "patient_querysets"
        ]["eligible"]:
            # Set all to None initially as updating as [True | False] if pt in [passed | failed]
            # querysets for each kpi -> if not in either, must mean they are ineligible (therefore None)
            data[pt.pk] = {kpi_attr_name: None for kpi_attr_name in kpi_attr_names}
            # Additional values we can calculate now
            data[pt.pk]["nhs_number"] = pt.nhs_number or pt.unique_reference_number or "Unknown"

        # For each kpi, update the data dict with the pts that have passed and failed
        for kpi_attr_name in kpi_attr_names:

            kpi_pt_querysets = kpi_calculations_object["calculated_kpi_values"][kpi_attr_name][
                "patient_querysets"
            ]

            for pt in kpi_pt_querysets["passed"]:
                data[pt.pk][kpi_attr_name] = True

            for pt in kpi_pt_querysets["failed"]:
                data[pt.pk][kpi_attr_name] = False

        # Finally add the headers. Need to add nhs_number

        headers = ["nhs_number"] + kpi_attr_names
        return headers, data

    elif category == "care_at_diagnosis":
        data = {}

        for kpi_attr_name in kpi_attr_names:

            kpi_pt_querysets = kpi_calculations_object["calculated_kpi_values"][kpi_attr_name][
                "patient_querysets"
            ]

            # For each kpi_attribute's eligible pts, add to data dict
            for pt in kpi_pt_querysets["eligible"]:
                # If pt not already in, initialise with None for all kpi_attr_names
                if data.get(pt.pk) is None:
                    data[pt.pk] = {kpi_attr_name: None for kpi_attr_name in kpi_attr_names}
                    data[pt.pk]["nhs_number"] = (
                        pt.nhs_number or pt.unique_reference_number or "Unknown"
                    )

            for pt in kpi_pt_querysets["passed"]:
                data[pt.pk][kpi_attr_name] = True
                data[pt.pk]["nhs_number"] = pt.nhs_number or pt.unique_reference_number or "Unknown"

            for pt in kpi_pt_querysets["failed"]:
                data[pt.pk][kpi_attr_name] = False
                data[pt.pk]["nhs_number"] = pt.nhs_number or pt.unique_reference_number or "Unknown"

        # Finally add the headers. Need to add nhs_number
        headers = ["nhs_number"] + kpi_attr_names

        return headers, data

    elif category == "outcomes":

        # Need to do some manual work as calculate_kpi methods perform aggregations of individual
        # pt values.

        # access helper methods
        get_median_hba1c_values_by_patient = (
            calculate_kpis_object.get_median_hba1c_values_by_patient
        )
        calculate_mean = calculate_kpis_object.calculate_mean

        # Get the base eligible pts (T1DM with complete year of care)
        kpi_pt_querysets = calculate_kpis_object.calculate_kpi_5_total_t1dm_complete_year().patient_querysets

        # Start with the median hba1c values
        data = get_median_hba1c_values_by_patient(kpi_pt_querysets["eligible"])

        # data looks like a dict with pt.pk as key and data as value
        # {
        #     164: {
        #         "hb1ac_values": [
        #             Decimal("85.00"),
        #             ...
        #             Decimal("74.00"),
        #         ],
        #         "median": 77.0, <------------------- median value
        #         "nhs_number": "4739254131",
        #     },
        #     165: {
        #         "hb1ac_values": [
        #             Decimal("78.00"),
        #             ...
        #             Decimal("59.00"),
        #         ],
        #         "median": 77.0,
        #         "nhs_number": "4373272123",
        #     },
        # }

        # Have enough to start constructing the data dict for the table

        for pt_pk in data:

            pt_data: dict = data[pt_pk]

            # Whilst iterating, need to also add 'mean' hba1c values per patient's values object
            hba1cs: list[Decimal] = pt_data.pop("hb1ac_values")
            data[pt_pk]["kpi_44_mean_hba1c"] = round(calculate_mean(hba1cs), 1)
            # Rename
            data[pt_pk]["kpi_45_median_hba1c"] = round(pt_data.pop("median"), 1)

            # Remaining kpis 46-49
            # NOTE: because each key is already all eligible pts, we just need to find
            # relevant values for each key

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

        # Finally add the headers. Need to add nhs_number
        headers = ["nhs_number"] + kpi_attr_names

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

        # Grab eligible patients (KPI 1, same for all)
        eligible_pts = kpi_calculations_object["calculated_kpi_values"][get_attribute_name(13)][
            "patient_querysets"
        ]["eligible"]

        # Start constructing the data dict

        for pt in eligible_pts:

            # Add nhs number
            data[pt.pk]["nhs_number"] = pt.nhs_number or pt.unique_reference_number or "Unknown"

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
                    kpi_calculations_object["calculated_kpi_values"][glucose_monitoring_kpi_attr][
                        "patient_querysets"
                    ]["passed"]
                    .filter(pk=pt.pk)
                    .exists()
                ):
                    data[pt.pk]["cgm"] = cgm_attr_vals_map[glucose_monitoring_kpi_attr]
                    break

            # HCL col -> true or false
            data[pt.pk][get_attribute_name(24)] = (
                kpi_calculations_object["calculated_kpi_values"][get_attribute_name(24)][
                    "patient_querysets"
                ]["passed"]
                .filter(pk=pt.pk)
                .exists()
            )

        # Finally add the headers. Need to add nhs_number
        headers = ["nhs_number", "tx_regimen", "cgm", get_attribute_name(24)]

        return headers, dict(data)

    raise NotImplementedError(f"Category {category} not yet implemented")
