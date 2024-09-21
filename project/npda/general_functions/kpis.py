"""Views for KPIs

TODO:
    - refactor all calculate_kpi methods which require kpi_1 base query set to use
      _get_total_kpi_1_eligible_pts_base_query_set_and_total_count
        - additionally, do same for any other reused attrs
"""

import logging
# Python imports
import time
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
from typing import Tuple

from dateutil.relativedelta import relativedelta
from django.db.models import OuterRef, Q, QuerySet, Subquery
from django.http import JsonResponse
# Django imports
from django.shortcuts import render
from django.views.generic import TemplateView

# NPDA Imports
from project.constants.diabetes_types import DIABETES_TYPES
from project.constants.retinal_screening_results import \
    RETINAL_SCREENING_RESULTS
from project.npda.general_functions import get_audit_period_for_date
from project.npda.general_functions.kpis_calculations import (
    kpi_2_total_new_diagnoses, kpi_3_total_t1dm, kpi_4_total_t1dm_gte_12yo,
    kpi_5_total_t1dm_complete_year, kpi_6_total_t1dm_complete_year_gte_12yo,
    kpi_7_total_new_diagnoses_t1dm, kpi_8_total_deaths,
    kpi_9_total_service_transitions, kpi_10_total_coeliacs,
    kpi_11_total_thyroids, kpi_12_total_ketone_test_equipment,
    kpi_13_one_to_three_injections_per_day,
    kpi_14_four_or_more_injections_per_day, kpi_15_insulin_pump,
    kpi_16_one_to_three_injections_plus_other_medication,
    kpi_17_four_or_more_injections_plus_other_medication,
    kpi_18_insulin_pump_plus_other_medication, kpi_19_dietary_management_alone,
    kpi_20_dietary_management_plus_other_medication,
    kpi_21_flash_glucose_monitor, kpi_22_real_time_cgm_with_alarms,
    kpi_23_type1_real_time_cgm_with_alarms, kpi_24_hybrid_closed_loop_system,
    kpi_25_hba1c, kpi_26_bmi, kpi_27_thyroid_screen, kpi_28_blood_pressure,
    kpi_29_urinary_albumin, kpi_30_retinal_screening, kpi_31_foot_examination,
    kpi_32_health_check_completion_rate, kpi_33_hba1c_4plus,
    kpi_34_psychological_assessment, kpi_35_smoking_status_screened,
    kpi_36_referral_to_smoking_cessation_service,
    kpi_37_additional_dietetic_appointment_offered,
    kpi_38_patients_attending_additional_dietetic_appointment,
    kpi_39_influenza_immunisation_recommended, kpi_40_sick_day_rules_advice,
    kpi_41_coeliac_disease_screening, kpi_42_thyroid_disease_screening,
    kpi_43_carbohydrate_counting_education, kpi_44_mean_hba1c,
    kpi_45_median_hba1c, kpi_46_number_of_admissions,
    kpi_47_number_of_dka_admissions,
    kpi_48_required_additional_psychological_support,
    kpi_49_albuminuria_present)
from project.npda.models import Patient
from project.npda.models.transfer import Transfer
from project.npda.models.visit import Visit

# Logging
logger = logging.getLogger(__name__)


# Object types
@dataclass
class KPIResult:
    total_eligible: int
    total_ineligible: int
    total_passed: int
    total_failed: int


class CalculateKPIS:

    def __init__(self, pz_code: str, calculation_date: date = None):
        """Calculates KPIs for given pz_code

        Params:
            * pz_code (str) - PZ code for KPIS
            * calculation_date (date) - used to define start and end date of audit period
        """
        if not pz_code:
            raise AttributeError("pz_code must be provided")
        # Set various attributes used in calculations
        self.pz_code = pz_code
        self.calculation_date = (
            calculation_date if calculation_date is not None else date.today()
        )
        # Set the start and end audit dates
        self.audit_start_date, self.audit_end_date = (
            self._get_audit_start_and_end_dates()
        )
        self.AUDIT_DATE_RANGE = (self.audit_start_date, self.audit_end_date)

        # Sets the KPI attribute names map
        self.kpis_names_map = self._get_kpi_attribute_names()

        # Sets relevant patients for this PZ code
        # NOTE: the first `paediatric_diabetes_units` uses the `related_name` from the
        # `Transfer` link table, the second `paediatric_diabetes_unit` actually
        # accesses the `PaediatricDiabetesUnit` model.
        # TODO: should this filter out patients who have left the service?
        self.patients = Patient.objects.filter(
            paediatric_diabetes_units__paediatric_diabetes_unit__pz_code=pz_code
        ).distinct()
        self.total_patients_count = self.patients.count()

    def _get_audit_start_and_end_dates(self) -> tuple[date, date]:
        return get_audit_period_for_date(input_date=self.calculation_date)

    def _get_kpi_attribute_names(self) -> dict[int, str]:
        """
        Hard coding these for simplicty and readability

        KPIS
        1-12
            - used as denominators for subsequent
        13-20
            - treatment regimen
        21-23
            - glucose monitoring
        24
            - Hybrid closed loop system (HCL)
        25-32
            - 7 key processes
        33-40
            - additional processes
        41-43
            - care at diagnosis
        44-49
            - outcomes
        """

        kpis = {
            1: "kpi_1_total_eligible",
            2: "kpi_2_total_new_diagnoses",
            3: "kpi_3_total_t1dm",
            4: "kpi_4_total_t1dm_gte_12yo",
            5: "kpi_5_total_t1dm_complete_year",
            6: "kpi_6_total_t1dm_complete_year_gte_12yo",
            7: "kpi_7_total_new_diagnoses_t1dm",
            8: "kpi_8_total_deaths",
            9: "kpi_9_total_service_transitions",
            10: "kpi_10_total_coeliacs",
            11: "kpi_11_total_thyroids",
            12: "kpi_12_total_ketone_test_equipment",
            13: "kpi_13_one_to_three_injections_per_day",
            14: "kpi_14_four_or_more_injections_per_day",
            15: "kpi_15_insulin_pump",
            16: "kpi_16_one_to_three_injections_plus_other_medication",
            17: "kpi_17_four_or_more_injections_plus_other_medication",
            18: "kpi_18_insulin_pump_plus_other_medication",
            19: "kpi_19_dietary_management_alone",
            20: "kpi_20_dietary_management_plus_other_medication",
            21: "kpi_21_flash_glucose_monitor",
            22: "kpi_22_real_time_cgm_with_alarms",
            23: "kpi_23_type1_real_time_cgm_with_alarms",
            24: "kpi_24_hybrid_closed_loop_system",
            25: "kpi_25_hba1c",
            26: "kpi_26_bmi",
            27: "kpi_27_thyroid_screen",
            28: "kpi_28_blood_pressure",
            29: "kpi_29_urinary_albumin",
            30: "kpi_30_retinal_screening",
            31: "kpi_31_foot_examination",
            321: "kpi_32_1_health_check_completion_rate",
            322: "kpi_32_2_health_check_lt_12yo",
            323: "kpi_32_3_health_check_gte_12yo",
            33: "kpi_33_hba1c_4plus",
            34: "kpi_34_psychological_assessment",
            35: "kpi_35_smoking_status_screened",
            36: "kpi_36_referral_to_smoking_cessation_service",
            37: "kpi_37_additional_dietetic_appointment_offered",
            38: "kpi_38_patients_attending_additional_dietetic_appointment",
            39: "kpi_39_influenza_immunisation_recommended",
            40: "kpi_40_sick_day_rules_advice",
            41: "kpi_41_coeliac_disease_screening",
            42: "kpi_42_thyroid_disease_screening",
            43: "kpi_43_carbohydrate_counting_education",
            44: "kpi_44_mean_hba1c",
            45: "kpi_45_median_hba1c",
            46: "kpi_46_number_of_admissions",
            47: "kpi_47_number_of_dka_admissions",
            48: "kpi_48_required_additional_psychological_support",
            49: "kpi_49_albuminuria_present",
        }

        return kpis

    def calculate_kpis_for_patients(self) -> dict:
        """Calculate KPIs for given self.pz_code and cohort range
        (self.audit_start_date and self.audit_end_date).

        We dynamically set these attributes using names set in self.kpis, done in
        the self._get_kpi_attribute_names method during object init.

        Incrementally build the query, which will be executed in a single
        transaction once a value is evaluated.
        """

        calculated_kpis = {}

        # Calculate KPIs 1 - 49
        for i in range(1, 50):
            # Dynamically get the method name from the kpis_names_map
            kpi_method_name = self.kpis_names_map[i]
            kpi_method = getattr(self, f"calculate_{kpi_method_name}", None)

            # If the method is not implemented, set the value to "Not implemented"
            # and skip
            if kpi_method is None:
                calculated_kpis[kpi_method_name] = "Not implemented"
                continue

            # Else, calculate the KPI
            kpi_result = kpi_method()

            # Validations
            if not is_dataclass(kpi_result):
                raise TypeError(
                    f"kpi_result is not a dataclass instance: {kpi_result} (type: {type(kpi_result)})"
                )
            if not isinstance(kpi_result, KPIResult):
                raise TypeError(
                    f"kpi_result is not an instance of KPIResult: {kpi_result} (type: {type(kpi_result)})"
                )

            # Each kpi method returns a KPIResult object
            # so we convert it first to a dictionary
            calculated_kpis[kpi_method_name] = asdict(kpi_result)

        # Add in used attributes for calculations
        return_obj = {}
        return_obj["pz_code"] = self.pz_code
        return_obj["calculation_datetime"] = datetime.now()
        return_obj["audit_start_date"] = self.audit_start_date
        return_obj["audit_end_date"] = self.audit_end_date
        return_obj["total_patients_count"] = self.total_patients_count

        # Finally, add in the kpis
        return_obj["calculated_kpi_values"] = {}
        for kpi_name, kpi_result in calculated_kpis.items():
            return_obj["calculated_kpi_values"][kpi_name] = kpi_result

        return return_obj

    def calculate_kpi_1_total_eligible(self) -> KPIResult:
        """
        Calculates KPI 1: Total number of eligible patients
        Total number of patients with:
            * a valid NHS number
            * a valid date of birth
            * a valid PDU number
            * a visit date or admission date within the audit period
            * Below the age of 25 at the start of the audit period
        """

        # Set the query set as an attribute to be used in subsequent KPI calculations
        self.total_kpi_1_eligible_pts_base_query_set = self.patients.filter(
            # Valid attributes
            Q(nhs_number__isnull=False)
            & Q(date_of_birth__isnull=False)
            # Visit / admisison date within audit period
            & Q(visit__visit_date__range=(self.AUDIT_DATE_RANGE))
            # Below the age of 25 at the start of the audit period
            & Q(
                date_of_birth__gt=self.audit_start_date
                - relativedelta(years=25)
            )
        )

        eligible_patients = (
            self.total_kpi_1_eligible_pts_base_query_set.distinct()
        )
        self.kpi_1_total_eligible = eligible_patients.count()

        # Count eligible patients and set as attribute
        # to be used in subsequent KPI calculations
        total_eligible = self.kpi_1_total_eligible

        # Calculate ineligible patients
        total_ineligible = self.total_patients_count - total_eligible

        # Assuming total_passed is equal to total_number_of_eligible_patients_kpi_1 and total_failed is equal to total_ineligible
        total_passed = total_eligible
        total_failed = total_ineligible

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_2_total_new_diagnoses(self) -> KPIResult:
        """
        Calculates KPI 2: Total number of new diagnoses within the audit period

        "Total number of patients with:
        * a valid NHS number
        *a valid date of birth
        *a valid PDU number
        * a visit date or admission date within the audit period
        * Below the age of 25 at the start of the audit period
        * Date of diagnosis within the audit period"
        """

        # If we have not already calculated KPI 1, do so now to set
        # self.total_kpi_1_eligible_pts_base_query_set
        if not hasattr(self, "total_kpi_1_eligible_pts_base_query_set"):
            self.calculate_kpi_1_total_eligible()

        # This is same as KPI1 but with an additional filter for diagnosis date
        self.total_kpi_2_eligible_pts_base_query_set = (
            self.total_kpi_1_eligible_pts_base_query_set.filter(
                Q(diagnosis_date__range=(self.AUDIT_DATE_RANGE))
            ).distinct()
        )

        # Count eligible patients
        self.kpi_2_total_eligible = (
            self.total_kpi_2_eligible_pts_base_query_set.count()
        )
        total_eligible = self.kpi_2_total_eligible

        # Calculate ineligible patients
        total_ineligible = self.total_patients_count - total_eligible

        # This is just a count so pass/fail doesn't make sense; just set to same
        # as eligible/ineligible
        total_passed = total_eligible
        total_failed = total_ineligible

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_3_total_t1dm(self) -> KPIResult:
        """
        Calculates KPI 3: Total number of eligible patients with Type 1 diabetes
        Total number of patients with:
            * a valid NHS number
            *a valid date of birth
            *a valid PDU number
            * a visit date or admission date within the audit period
            * Below the age of 25 at the start of the audit period
            * Diagnosis of Type 1 diabetes"

        (1, Type 1 Insulin-Dependent Diabetes Mellitus)
        """
        eligible_patients = self.total_kpi_1_eligible_pts_base_query_set.filter(
            # is type 1 diabetes
            Q(diabetes_type=DIABETES_TYPES[0][0])
        ).distinct()

        # Count eligible patients
        total_eligible = eligible_patients.count()

        # Calculate ineligible patients
        total_ineligible = self.total_patients_count - total_eligible

        # This is just a count so pass/fail doesn't make sense; just set to same
        # as eligible/ineligible
        total_passed = total_eligible
        total_failed = total_ineligible

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_4_total_t1dm_gte_12yo(self) -> KPIResult:
        """
        Calculates KPI 4: Number of patients aged 12+ with Type 1 diabetes
        Total number of patients with:
            * a valid NHS number
            *a valid date of birth
            *a valid PDU number
            * a visit date or admission date within the audit period
            * Below the age of 25 at the start of the audit period
            * Age 12 and above years at the start of the audit period
            * Diagnosis of Type 1 diabetes"
        """

        eligible_patients = self.total_kpi_1_eligible_pts_base_query_set.filter(
            # Diagnosis of Type 1 diabetes
            Q(diabetes_type=DIABETES_TYPES[0][0])
            # Age 12 and above years at the start of the audit period
            & Q(
                date_of_birth__lte=self.audit_start_date
                - relativedelta(years=12)
            )
        ).distinct()

        # Count eligible patients
        total_eligible = eligible_patients.count()

        # Calculate ineligible patients
        total_ineligible = self.total_patients_count - total_eligible

        # This is just a count so pass/fail doesn't make sense; just set to same
        # as eligible/ineligible
        total_passed = total_eligible
        total_failed = total_ineligible

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_5_total_t1dm_complete_year(self) -> KPIResult:
        """
        Calculates KPI 5: Total number of patients with T1DM who have completed a year of care
        "Total number of patients with:
        * a valid NHS number
        *a valid date of birth
        *a valid PDU number
        * a visit date or admission date within the audit period
        * Below the age of 25 at the start of the audit period* Diagnosis of Type 1 diabetes

        Excluding
        * Date of diagnosis within the audit period
        * Date of leaving service within the audit period
        * Date of death within the audit period"
        """
        # If we have not already calculated KPI 1, do so now to set
        total_kpi_1_eligible_pts_base_query_set, total_eligible_kpi_1 = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = total_kpi_1_eligible_pts_base_query_set.exclude(
            # EXCLUDE Date of diagnosis within the audit period
            Q(diagnosis_date__range=(self.AUDIT_DATE_RANGE))
            # EXCLUDE Date of leaving service within the audit period
            | (
                Q(
                    paediatric_diabetes_units__date_leaving_service__range=(
                        self.audit_start_date,
                        self.audit_end_date,
                    )
                )
            )
            # EXCLUDE Date of death within the audit period"
            | Q(death_date__range=(self.AUDIT_DATE_RANGE))
        ).distinct()

        # Count eligible patients
        total_eligible = eligible_patients.count()
        # We also use this as denominator for subsequent KPIS
        # so set as attributes
        self.total_kpi_5_eligible_pts_base_query_set = eligible_patients
        self.kpi_5_total_eligible = total_eligible

        # Calculate ineligible patients
        total_ineligible = self.total_patients_count - total_eligible

        # This is just a count so pass/fail doesn't make sense; just set to same
        # as eligible/ineligible
        total_passed = total_eligible
        total_failed = total_ineligible

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_6_total_t1dm_complete_year_gte_12yo(self) -> dict:
        """
        Calculates KPI 6: Total number of patients with T1DM who have completed a year of care and are aged 12 or older
        Total number of patients with:
        * a valid NHS number
        * an observation within the audit period
        * Age 12 and above at the start of the audit period
        * Diagnosis of Type 1 diabetes

        Excluding
        * Date of diagnosis within the audit period
        * Date of leaving service within the audit period
        * Date of death within the audit period

        NOTE: exclusion same as KPI5
        """

        # We cannot simply use KPI1 base queryset as that includes a filter
        # for age < 25. Additionally, this requires an observation within
        # the audit period, which is not included in KPI1 base queryset.
        # So need to make new query set

        # Separate exclusions from the main query for clarity
        eligible_patients_exclusions = self.patients.exclude(
            # EXCLUDE Date of diagnosis within the audit period
            Q(diagnosis_date__range=(self.AUDIT_DATE_RANGE))
            # EXCLUDE Date of leaving service within the audit period
            | (
                Q(
                    paediatric_diabetes_units__date_leaving_service__range=(
                        self.audit_start_date,
                        self.audit_end_date,
                    )
                )
            )
            # EXCLUDE Date of death within the audit period"
            | Q(death_date__range=(self.AUDIT_DATE_RANGE))
        )

        eligible_patients = eligible_patients_exclusions.filter(
            # Valid attributes
            Q(nhs_number__isnull=False)
            & Q(date_of_birth__isnull=False)
            # Age 12 and above at the start of the audit period
            & Q(
                date_of_birth__lte=self.audit_start_date
                - relativedelta(years=12)
            )
            # Diagnosis of Type 1 diabetes
            & Q(diabetes_type=DIABETES_TYPES[0][0])
            & (
                # an observation within the audit period
                # this requires checking for a date in any of the Visit model's
                # observation fields (found simply by searching for date fields
                # with the word 'observation' in the field verbose_name)
                Q(
                    visit__height_weight_observation_date__range=(
                        self.AUDIT_DATE_RANGE
                    )
                )
                | Q(visit__hba1c_date__range=(self.AUDIT_DATE_RANGE))
                | Q(
                    visit__blood_pressure_observation_date__range=(
                        self.AUDIT_DATE_RANGE
                    )
                )
                | Q(
                    visit__foot_examination_observation_date__range=(
                        self.AUDIT_DATE_RANGE
                    )
                )
                | Q(
                    visit__retinal_screening_observation_date__range=(
                        self.AUDIT_DATE_RANGE
                    )
                )
                | Q(
                    visit__albumin_creatinine_ratio_date__range=(
                        self.AUDIT_DATE_RANGE
                    )
                )
                | Q(
                    visit__total_cholesterol_date__range=(
                        self.AUDIT_DATE_RANGE
                    )
                )
                | Q(
                    visit__thyroid_function_date__range=(self.AUDIT_DATE_RANGE)
                )
                | Q(visit__coeliac_screen_date__range=(self.AUDIT_DATE_RANGE))
                | Q(
                    visit__psychological_screening_assessment_date__range=(
                        self.AUDIT_DATE_RANGE
                    )
                )
            )
        ).distinct()

        # Count eligible patients
        total_eligible = eligible_patients.count()

        # In case we need to use this as a base query set for subsequent KPIs
        self.total_kpi_6_eligible_pts_base_query_set = eligible_patients
        self.kpi_6_total_eligible = total_eligible

        # Calculate ineligible patients
        total_ineligible = self.total_patients_count - total_eligible

        # This is just a count so pass/fail doesn't make sense; just set to same
        # as eligible/ineligible
        total_passed = total_eligible
        total_failed = total_ineligible

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_7_total_new_diagnoses_t1dm(self) -> dict:
        """
        Calculates KPI 7: Total number of new diagnoses of T1DM
        Total number of patients with:
        * a valid NHS number
        * an observation within the audit period
        * Age 0-24 years at the start of the audit period
        * Diagnosis of Type 1 diabetes
        * Date of diagnosis within the audit period
        """

        # total_kpi_1_eligible_pts_base_query_set is slightly different (additionally specifies
        # visit date). So we need to make a new query set
        eligible_patients = self.patients.filter(
            # Valid attributes
            Q(nhs_number__isnull=False)
            & Q(date_of_birth__isnull=False)
            # * Age < 25y years at the start of the audit period
            & Q(
                date_of_birth__gt=self.audit_start_date
                - relativedelta(years=25)
            )
            # Diagnosis of Type 1 diabetes
            & Q(diabetes_type=DIABETES_TYPES[0][0])
            & Q(diagnosis_date__range=self.AUDIT_DATE_RANGE)
            & (
                # an observation within the audit period
                # this requires checking for a date in any of the Visit model's
                # observation fields (found simply by searching for date fields
                # with the word 'observation' in the field verbose_name)
                Q(
                    visit__height_weight_observation_date__range=(
                        self.AUDIT_DATE_RANGE
                    )
                )
                | Q(visit__hba1c_date__range=(self.AUDIT_DATE_RANGE))
                | Q(
                    visit__blood_pressure_observation_date__range=(
                        self.AUDIT_DATE_RANGE
                    )
                )
                | Q(
                    visit__foot_examination_observation_date__range=(
                        self.AUDIT_DATE_RANGE
                    )
                )
                | Q(
                    visit__retinal_screening_observation_date__range=(
                        self.AUDIT_DATE_RANGE
                    )
                )
                | Q(
                    visit__albumin_creatinine_ratio_date__range=(
                        self.AUDIT_DATE_RANGE
                    )
                )
                | Q(
                    visit__total_cholesterol_date__range=(
                        self.AUDIT_DATE_RANGE
                    )
                )
                | Q(
                    visit__thyroid_function_date__range=(self.AUDIT_DATE_RANGE)
                )
                | Q(visit__coeliac_screen_date__range=(self.AUDIT_DATE_RANGE))
                | Q(
                    visit__psychological_screening_assessment_date__range=(
                        self.AUDIT_DATE_RANGE
                    )
                )
            )
        ).distinct()

        # Count eligible patients
        total_eligible = eligible_patients.count()

        # Calculate ineligible patients
        total_ineligible = self.total_patients_count - total_eligible

        # This is just a count so pass/fail doesn't make sense; just set to same
        # as eligible/ineligible
        total_passed = total_eligible
        total_failed = total_ineligible

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_8_total_deaths(self) -> dict:
        """
        Calculates KPI 8: Number of patients who died within audit period
        Number of eligible patients (measure 1) with:
            * a death date in the audit period
        """
        eligible_patients = self.total_kpi_1_eligible_pts_base_query_set.filter(
            # Date of death within the audit period"
            Q(death_date__range=(self.AUDIT_DATE_RANGE))
        ).distinct()

        # Count eligible patients
        total_eligible = eligible_patients.count()

        # Calculate ineligible patients
        total_ineligible = self.total_patients_count - total_eligible

        # This is just a count so pass/fail doesn't make sense; just set to same
        # as eligible/ineligible
        total_passed = total_eligible
        total_failed = total_ineligible

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_9_total_service_transitions(self) -> dict:
        """
        Calculates KPI 9: Number of patients who transitioned/left service within audit period

        Number of eligible patients (measure 1) with
        * a leaving date in the audit period
        """
        eligible_patients = self.total_kpi_1_eligible_pts_base_query_set.filter(
            # a leaving date in the audit period
            Q(
                paediatric_diabetes_units__date_leaving_service__range=(
                    self.AUDIT_DATE_RANGE
                )
            )
        ).distinct()

        # Count eligible patients
        total_eligible = eligible_patients.count()

        # Calculate ineligible patients
        total_ineligible = self.total_patients_count - total_eligible

        # This is just a count so pass/fail doesn't make sense; just set to same
        # as eligible/ineligible
        total_passed = total_eligible
        total_failed = total_ineligible

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_10_total_coeliacs(self) -> dict:
        """
        Calculates KPI 10: Total number of coeliacs
        Number of eligible patients (measure 1) who:

        * most recent observation for item 37 (based on visit date) is 1 = Yes
        // NOTE: item37 is _Has the patient been recommended a Gluten-free diet? _
        """
        # Define the subquery to find the latest visit where visit__gluten_free_diet = 1
        latest_visit_subquery = (
            Visit.objects.filter(patient=OuterRef("pk"), gluten_free_diet=1)
            .order_by("-visit_date")
            .values("pk")[:1]
        )

        # Filter the Patient queryset based on the subquery
        eligible_patients = (
            self.total_kpi_1_eligible_pts_base_query_set.filter(
                Q(
                    id__in=Subquery(
                        Patient.objects.filter(
                            visit__in=latest_visit_subquery
                        ).values("id")
                    )
                )
            )
        )

        # Count eligible patients
        total_eligible = eligible_patients.count()

        # Calculate ineligible patients
        total_ineligible = self.total_patients_count - total_eligible

        # This is just a count so pass/fail doesn't make sense; just set to same
        # as eligible/ineligible
        total_passed = total_eligible
        total_failed = total_ineligible

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_11_total_thyroids(self) -> dict:
        """
        Calculates KPI 11: Number of patients with thyroid  disease
        Number of eligible patients (measure 1)
        who:
            * most recent observation for item 35 (based on visit date) is either 2 = Thyroxine for hypothyroidism or 3 = Antithyroid medication for hyperthyroidism
            // NOTE: item35 is _At time of, or following measurement of thyroid function, was the patient prescribed any thyroid treatment?_
        """
        # Define the subquery to find the latest visit where thyroid_treatment_status__in = 2 or 3
        latest_visit_subquery = (
            Visit.objects.filter(
                patient=OuterRef("pk"), thyroid_treatment_status__in=[2, 3]
            )
            .order_by("-visit_date")
            .values("pk")[:1]
        )

        # Filter the Patient queryset based on the subquery
        eligible_patients = (
            self.total_kpi_1_eligible_pts_base_query_set.filter(
                Q(
                    id__in=Subquery(
                        Patient.objects.filter(
                            visit__in=latest_visit_subquery
                        ).values("id")
                    )
                )
            )
        )

        # Count eligible patients
        total_eligible = eligible_patients.count()

        # Calculate ineligible patients
        total_ineligible = self.total_patients_count - total_eligible

        # This is just a count so pass/fail doesn't make sense; just set to same
        # as eligible/ineligible
        total_passed = total_eligible
        total_failed = total_ineligible

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_12_total_ketone_test_equipment(self) -> dict:
        """
        Calculates KPI 12: Number of patients using (or trained to use) blood ketone testing equipment

        Number of eligible patients (measure 1) whose
            * most recent observation for item 45 (based on visit date) is 1 = Yes
            // NOTE: item45 is _Was the patient using (or trained to use) blood ketone testing equipment at time of visit? _
        """
        # Define the subquery to find the latest visit where ketone_meter_training = 1
        latest_visit_subquery = (
            Visit.objects.filter(
                patient=OuterRef("pk"), ketone_meter_training=1
            )
            .order_by("-visit_date")
            .values("pk")[:1]
        )

        # Filter the Patient queryset based on the subquery
        eligible_patients = (
            self.total_kpi_1_eligible_pts_base_query_set.filter(
                Q(
                    id__in=Subquery(
                        Patient.objects.filter(
                            visit__in=latest_visit_subquery
                        ).values("id")
                    )
                )
            )
        )

        # Count eligible patients
        total_eligible = eligible_patients.count()

        # Calculate ineligible patients
        total_ineligible = self.total_patients_count - total_eligible

        # This is just a count so pass/fail doesn't make sense; just set to same
        # as eligible/ineligible
        total_passed = total_eligible
        total_failed = total_ineligible

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_13_one_to_three_injections_per_day(self) -> dict:
        """
        Calculates KPI 13: One - three injections/day

        Numerator: Number of eligible patients whose most recent entry (based on visit date)
        for treatment regimen (item 20) is 1 = One-three injections/day

        Denominator: Total number of eligible patients (measure 1)
        """
        eligible_patients = self.total_kpi_1_eligible_pts_base_query_set
        total_eligible = self.kpi_1_total_eligible
        total_ineligible = self.total_patients_count - total_eligible

        # Define the subquery to find the latest visit where treatment_regimen = 1
        latest_visit_subquery = (
            Visit.objects.filter(patient=OuterRef("pk"), treatment=1)
            .order_by("-visit_date")
            .values("pk")[:1]
        )
        # Filter the Patient queryset based on the subquery
        total_passed = eligible_patients.filter(
            Q(
                id__in=Subquery(
                    Patient.objects.filter(
                        visit__in=latest_visit_subquery
                    ).values("id")
                )
            )
        ).count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_14_four_or_more_injections_per_day(self) -> dict:
        """
        Calculates KPI 14: Four or more injections/day

        Numerator: Number of eligible patients whose most recent entry (based on visit date)
        for treatment regimen (item 20) is 2 = Four or more injections/day

        Denominator: Total number of eligible patients (measure 1)
        """
        eligible_patients = self.total_kpi_1_eligible_pts_base_query_set
        total_eligible = self.kpi_1_total_eligible
        total_ineligible = self.total_patients_count - total_eligible

        # Define the subquery to find the latest visit where treatment_regimen = 2
        latest_visit_subquery = (
            Visit.objects.filter(patient=OuterRef("pk"), treatment=2)
            .order_by("-visit_date")
            .values("pk")[:1]
        )
        # Filter the Patient queryset based on the subquery
        total_passed = eligible_patients.filter(
            Q(
                id__in=Subquery(
                    Patient.objects.filter(
                        visit__in=latest_visit_subquery
                    ).values("id")
                )
            )
        ).count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_15_insulin_pump(self) -> dict:
        """
        Calculates KPI 15: Insulin pump (including those using a pump as part of a hybrid closed loop)

        Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment
        regimen (item 20) is 3 = Insulin pump

        Denominator: Total number of eligible patients (measure 1)
        """
        eligible_patients = self.total_kpi_1_eligible_pts_base_query_set
        total_eligible = self.kpi_1_total_eligible
        total_ineligible = self.total_patients_count - total_eligible

        # Define the subquery to find the latest visit where treatment_regimen = 3
        latest_visit_subquery = (
            Visit.objects.filter(patient=OuterRef("pk"), treatment=3)
            .order_by("-visit_date")
            .values("pk")[:1]
        )
        # Filter the Patient queryset based on the subquery
        total_passed = eligible_patients.filter(
            Q(
                id__in=Subquery(
                    Patient.objects.filter(
                        visit__in=latest_visit_subquery
                    ).values("id")
                )
            )
        ).count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_16_one_to_three_injections_plus_other_medication(
        self,
    ) -> dict:
        """
        Calculates KPI 16: One - three injections/day plus other blood glucose lowering medication

        Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is 4 = One - three injections/day plus other blood glucose lowering medication

        Denominator: Total number of eligible patients (measure 1)
        """
        eligible_patients = self.total_kpi_1_eligible_pts_base_query_set
        total_eligible = self.kpi_1_total_eligible
        total_ineligible = self.total_patients_count - total_eligible

        # Define the subquery to find the latest visit where treatment_regimen = 4
        latest_visit_subquery = (
            Visit.objects.filter(patient=OuterRef("pk"), treatment=4)
            .order_by("-visit_date")
            .values("pk")[:1]
        )
        # Filter the Patient queryset based on the subquery
        total_passed = eligible_patients.filter(
            Q(
                id__in=Subquery(
                    Patient.objects.filter(
                        visit__in=latest_visit_subquery
                    ).values("id")
                )
            )
        ).count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_17_four_or_more_injections_plus_other_medication(
        self,
    ) -> dict:
        """
        Calculates KPI 17: Four or more injections/day plus other blood glucose lowering medication

        Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is 5 = Four or more injections/day plus other blood glucose lowering medication

        Denominator: Total number of eligible patients (measure 1)
        """
        eligible_patients = self.total_kpi_1_eligible_pts_base_query_set
        total_eligible = self.kpi_1_total_eligible
        total_ineligible = self.total_patients_count - total_eligible

        # Define the subquery to find the latest visit where treatment_regimen = 5
        latest_visit_subquery = (
            Visit.objects.filter(patient=OuterRef("pk"), treatment=5)
            .order_by("-visit_date")
            .values("pk")[:1]
        )
        # Filter the Patient queryset based on the subquery
        total_passed = eligible_patients.filter(
            Q(
                id__in=Subquery(
                    Patient.objects.filter(
                        visit__in=latest_visit_subquery
                    ).values("id")
                )
            )
        ).count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_18_insulin_pump_plus_other_medication(
        self,
    ) -> dict:
        """
        Calculates KPI 18: Insulin pump therapy plus other blood glucose lowering medication

        Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is 6 = Insulin pump therapy plus other blood glucose lowering medication

        Denominator: Total number of eligible patients (measure 1)
        """
        eligible_patients = self.total_kpi_1_eligible_pts_base_query_set
        total_eligible = self.kpi_1_total_eligible
        total_ineligible = self.total_patients_count - total_eligible

        # Define the subquery to find the latest visit where treatment_regimen = 6
        latest_visit_subquery = (
            Visit.objects.filter(patient=OuterRef("pk"), treatment=6)
            .order_by("-visit_date")
            .values("pk")[:1]
        )
        # Filter the Patient queryset based on the subquery
        total_passed = eligible_patients.filter(
            Q(
                id__in=Subquery(
                    Patient.objects.filter(
                        visit__in=latest_visit_subquery
                    ).values("id")
                )
            )
        ).count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_19_dietary_management_alone(
        self,
    ) -> dict:
        """
        Calculates KPI 19: Dietary management alone (no insulin or other diabetes related medication)

        Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is 7 = Dietary management alone (no insulin or other diabetes related medication)

        Denominator: Total number of eligible patients (measure 1)
        """
        eligible_patients = self.total_kpi_1_eligible_pts_base_query_set
        total_eligible = self.kpi_1_total_eligible
        total_ineligible = self.total_patients_count - total_eligible

        # Define the subquery to find the latest visit where treatment_regimen = 7
        latest_visit_subquery = (
            Visit.objects.filter(patient=OuterRef("pk"), treatment=7)
            .order_by("-visit_date")
            .values("pk")[:1]
        )
        # Filter the Patient queryset based on the subquery
        total_passed = eligible_patients.filter(
            Q(
                id__in=Subquery(
                    Patient.objects.filter(
                        visit__in=latest_visit_subquery
                    ).values("id")
                )
            )
        ).count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_20_dietary_management_plus_other_medication(
        self,
    ) -> dict:
        """
        Calculates KPI 20: Dietary management plus other blood glucose lowering medication (non Type-1 diabetes)

        Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is 8 = Dietary management plus other blood glucose lowering medication (non Type-1 diabetes)

        Denominator: Total number of eligible patients (measure 1)
        """
        eligible_patients = self.total_kpi_1_eligible_pts_base_query_set
        total_eligible = self.kpi_1_total_eligible
        total_ineligible = self.total_patients_count - total_eligible

        # Define the subquery to find the latest visit where treatment_regimen = 8
        latest_visit_subquery = (
            Visit.objects.filter(patient=OuterRef("pk"), treatment=8)
            .order_by("-visit_date")
            .values("pk")[:1]
        )
        # Filter the Patient queryset based on the subquery
        total_passed = eligible_patients.filter(
            Q(
                id__in=Subquery(
                    Patient.objects.filter(
                        visit__in=latest_visit_subquery
                    ).values("id")
                )
            )
        ).count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_21_flash_glucose_monitor(
        self,
    ) -> dict:
        """
        Calculates KPI 21: Number of patients using a flash glucose monitor

        Numerator: Number of eligible patients whose most recent entry (based on visit date) for blood glucose monitoring (item 22) is either 2 = Flash glucose monitor or 3 = Modified flash glucose monitor (e.g. with MiaoMiao, Blucon etc.)

        Denominator: Total number of eligible patients (measure 1)
        """
        eligible_patients = self.total_kpi_1_eligible_pts_base_query_set
        total_eligible = self.kpi_1_total_eligible
        total_ineligible = self.total_patients_count - total_eligible

        # Define the subquery to find the latest visit where blood glucose monitoring (item 22) is either 2 = Flash glucose monitor or 3 = Modified flash glucose monitor (e.g. with MiaoMiao, Blucon etc.)
        latest_visit_subquery = (
            Visit.objects.filter(
                patient=OuterRef("pk"), glucose_monitoring__in=[2, 3]
            )
            .order_by("-visit_date")
            .values("pk")[:1]
        )
        # Filter the Patient queryset based on the subquery
        total_passed = eligible_patients.filter(
            Q(
                id__in=Subquery(
                    Patient.objects.filter(
                        visit__in=latest_visit_subquery
                    ).values("id")
                )
            )
        ).count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_22_real_time_cgm_with_alarms(
        self,
    ) -> dict:
        """
        Calculates KPI 22: Number of patients using a real time continuous glucose monitor (CGM) with alarms

        Numerator: Number of eligible patients whose most recent entry (based on visit date) for blood glucose monitoring (item 22) is 4 = Real time continuous glucose monitor with alarms

        Denominator: Total number of eligible patients (measure 1)
        """
        eligible_patients = self.total_kpi_1_eligible_pts_base_query_set
        total_eligible = self.kpi_1_total_eligible
        total_ineligible = self.total_patients_count - total_eligible

        # Define the subquery to find the latest visit where blood glucose monitoring (item 22) is 4 = Real time continuous glucose monitor with alarms
        latest_visit_subquery = (
            Visit.objects.filter(patient=OuterRef("pk"), glucose_monitoring=4)
            .order_by("-visit_date")
            .values("pk")[:1]
        )
        # Filter the Patient queryset based on the subquery
        total_passed = eligible_patients.filter(
            Q(
                id__in=Subquery(
                    Patient.objects.filter(
                        visit__in=latest_visit_subquery
                    ).values("id")
                )
            )
        ).count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_23_type1_real_time_cgm_with_alarms(
        self,
    ) -> dict:
        """
        Calculates KPI 23: Number of patients with Type 1 diabetes using a real time continuous glucose monitor (CGM) with alarms

        Numerator: Total number of eligible patients with Type 1 diabetes (measure 2)

        Denominator: Number of eligible patients whose most recent entry (based on visit date) for blood glucose monitoring (item 22) is 4 = Real time continuous glucose monitor with alarms
        """
        # If running this method standalone, need to set self.kpi_2_total_eligible first
        # by running its calculation method
        if not hasattr(self, "kpi_2_total_eligible"):
            self.calculate_kpi_2_total_new_diagnoses()

        eligible_patients = self.total_kpi_2_eligible_pts_base_query_set
        total_eligible = self.kpi_2_total_eligible
        total_ineligible = self.total_patients_count - total_eligible

        # Define the subquery to find the latest visit where blood glucose monitoring (item 22) is 4 = Real time continuous glucose monitor with alarms
        latest_visit_subquery = (
            Visit.objects.filter(patient=OuterRef("pk"), glucose_monitoring=4)
            .order_by("-visit_date")
            .values("pk")[:1]
        )
        # Filter the Patient queryset based on the subquery
        total_passed = eligible_patients.filter(
            Q(
                id__in=Subquery(
                    Patient.objects.filter(
                        visit__in=latest_visit_subquery
                    ).values("id")
                )
            )
        ).count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_24_hybrid_closed_loop_system(
        self,
    ) -> dict:
        """
        TODO: this was a little confusing, should be rechecked
                but tests are passing. # Issue 269 https://github.com/orgs/rcpch/projects/13/views/1?pane=issue&itemId=78574146

        Calculates KPI 24: Hybrid closed loop system (HCL)

        Denominator: Total number of eligible patients (measure 1)

        Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is either
            * 3 = insulin pump
            * or 6 = Insulin pump therapy plus other blood glucose lowering medication

            AND whose most recent entry for item 21 (based on visit date) is either
            * 2 = Closed loop system (licenced)
            * or 3 = Closed loop system (DIY, unlicenced)
            * or 4 = Closed loop system (licence status unknown)
        """
        # Denominator
        total_kpi_1_eligible_pts_base_query_set, total_eligible_kpi_1 = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )

        # Eligible kpi24 patients are those who are either on an insulin pump or insulin pump therapy
        eligible_kpi_24_latest_visit_subquery = (
            Visit.objects.filter(patient=OuterRef("pk"))
            .filter(
                # Either:
                # 3 = insulin pump
                # or 6 = Insulin pump therapy plus other blood glucose lowering medication
                Q(treatment__in=[3, 6])
            )
            .order_by("-visit_date")
            .values("pk")[:1]
        )
        eligible_patients_kpi_24 = (
            total_kpi_1_eligible_pts_base_query_set.filter(
                Q(
                    id__in=Subquery(
                        Patient.objects.filter(
                            visit__in=eligible_kpi_24_latest_visit_subquery
                        ).values("id")
                    )
                )
            )
        )
        total_eligible_kpi_24 = eligible_patients_kpi_24.count()

        # So ineligible patients are
        #   patients already ineligible for KPI 1
        #   PLUS
        #   the subset of total_kpi_1_eligible_pts_base_query_set
        #   who are ineligible for kpi24 (not on an insulin pump or insulin pump therapy)
        total_ineligible = (
            self.total_patients_count - total_eligible_kpi_1
        ) + (total_eligible_kpi_1 - total_eligible_kpi_24)

        # Passing patients are the subset of kpi_24 eligible who are on closed loop system
        passing_patients = eligible_patients_kpi_24.filter(
            Q(
                id__in=Subquery(
                    Patient.objects.filter(
                        Q(visit__in=eligible_kpi_24_latest_visit_subquery)
                        # AND whose most recent entry for item 21 (based on visit date) is either
                        # * 2 = Closed loop system (licenced)
                        # * or 3 = Closed loop system (DIY, unlicenced)
                        # * or 4 = Closed loop system (licence status unknown)
                        & Q(visit__closed_loop_system__in=[2, 3, 4])
                    ).values("id")
                )
            )
        )
        total_passed = passing_patients.count()
        total_failed = eligible_patients_kpi_24.count() - total_passed

        # logger.debug(f"passing_patients: {passing_patients.values_list('postcode')}")
        # logger.debug(f'{eligible_patients_kpi_24.values_list("postcode")=}')
        # logger.debug(
        #     f"{total_eligible_kpi_24, total_ineligible,total_passed,total_failed=}"
        # )

        return KPIResult(
            total_eligible=total_eligible_kpi_24,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_25_hba1c(
        self,
    ) -> dict:
        """
        Calculates KPI 25: HbA1c (%)


        Numerator: Number of eligible patients with at least one valid entry for HbA1c value (item 17) with an observation date (item 19) within the audit period

        Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
        """
        kpi_5_total_eligible_query_set, total_eligible_kpi_5 = (
            self._get_total_kpi_5_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = kpi_5_total_eligible_query_set
        total_eligible = total_eligible_kpi_5
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with at least one valid entry for HbA1c value (item 17) with an observation date (item 19) within the audit period
        # This is simply patients with a visit with a valid HbA1c value
        total_passed = eligible_patients.filter(
            Q(visit__hba1c__isnull=False),
            Q(visit__hba1c_date__range=(self.AUDIT_DATE_RANGE)),
        ).count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_26_bmi(
        self,
    ) -> dict:
        """
        # TODO: query - for 7 key processes KPIs (25-32), should we be
        # querying all visits for a patient? or is current implementation fine?

        Calculates KPI 26: BMI (%)

        Numerator: Number of eligible patients at least one valid entry for Patient Height (item 14) and for Patient Weight (item 15) with an observation date (item 16) within the audit period

        Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
        """
        kpi_5_total_eligible_query_set, total_eligible_kpi_5 = (
            self._get_total_kpi_5_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = kpi_5_total_eligible_query_set
        total_eligible = total_eligible_kpi_5
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with at least one valid entry for ht & wt within audit period
        total_passed_query_set = eligible_patients.filter(
            Q(visit__height__isnull=False),
            Q(visit__weight__isnull=False),
            # Within audit period
            Q(
                visit__height_weight_observation_date__range=(
                    self.AUDIT_DATE_RANGE
                )
            ),
        )

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_27_thyroid_screen(
        self,
    ) -> dict:
        """
        Calculates KPI 27: Thyroid Screen (%)

        Numerator: Number of eligible patients with at least one entry for Thyroid function observation date (item 34) within the audit period

        Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
        """
        kpi_5_total_eligible_query_set, total_eligible_kpi_5 = (
            self._get_total_kpi_5_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = kpi_5_total_eligible_query_set
        total_eligible = total_eligible_kpi_5
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with at least one valid entry for thyroid screen within audit period
        total_passed_query_set = eligible_patients.filter(
            # Within audit period
            Q(visit__thyroid_function_date__range=(self.AUDIT_DATE_RANGE)),
        )

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_28_blood_pressure(
        self,
    ) -> dict:
        """
        Calculates KPI 28: Blood Pressure (%)

        Numerator: Number of eligible patients with a valid entry for systolic measurement (item 23) with an observation date (item 25) within the audit period

        Denominator: Number of patients with Type 1 diabetes aged 12+ with a complete year of care in audit period (measure 6)

        # NOTE: Does not need a valid diastolic measurement
        """
        kpi_6_total_eligible_query_set, total_eligible_kpi_6 = (
            self._get_total_kpi_6_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = kpi_6_total_eligible_query_set
        total_eligible = total_eligible_kpi_6
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with at least one valid entry for systolic measurement within audit period
        total_passed_query_set = eligible_patients.filter(
            # Within audit period
            Q(visit__systolic_blood_pressure__isnull=False),
            Q(
                visit__blood_pressure_observation_date__range=(
                    self.AUDIT_DATE_RANGE
                )
            ),
        )

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_29_urinary_albumin(
        self,
    ) -> dict:
        """
        Calculates KPI 29: Urinary Albumin (%)

        Numerator: Number of eligible patients with at entry for Urinary Albumin Level (item 29) with an observation date (item 30) within the audit period

        Denominator: Number of patients with Type 1 diabetes aged 12+ with a complete year of care in audit period (measure 6)
        """
        kpi_6_total_eligible_query_set, total_eligible_kpi_6 = (
            self._get_total_kpi_6_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = kpi_6_total_eligible_query_set
        total_eligible = total_eligible_kpi_6
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with at least one valid entry for Urinary Albumin Level (item 29)
        # with an observation date (item 30) within the audit period
        total_passed_query_set = eligible_patients.filter(
            Q(visit__albumin_creatinine_ratio__isnull=False),
            # Within audit period
            Q(
                visit__albumin_creatinine_ratio_date__range=(
                    self.AUDIT_DATE_RANGE
                )
            ),
        )

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_30_retinal_screening(
        self,
    ) -> dict:
        """
        Calculates KPI 30: Retinal Screening (%)

        Numerator: Number of eligible patients with at least one entry for Retinal Screening Result (item 28) is either 1 = Normal or 2 = Abnormal AND the observation date (item 27) is within the audit period

        Denominator: Number of patients with Type 1 diabetes aged 12+ with a complete year of care in audit period (measure 6)
        """
        kpi_6_total_eligible_query_set, total_eligible_kpi_6 = (
            self._get_total_kpi_6_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = kpi_6_total_eligible_query_set
        total_eligible = total_eligible_kpi_6
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with at least one for Retinal Screening Result (item 28) is either 1 = Normal or 2 = Abnormal AND the observation date (item 27) is within the audit period
        total_passed_query_set = eligible_patients.filter(
            Q(
                visit__retinal_screening_result__in=[
                    RETINAL_SCREENING_RESULTS[0][0],
                    RETINAL_SCREENING_RESULTS[1][0],
                ]
            ),
            # Within audit period
            Q(
                visit__retinal_screening_observation_date__range=(
                    self.AUDIT_DATE_RANGE
                )
            ),
        )

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_31_foot_examination(
        self,
    ) -> dict:
        """
        Calculates KPI 31: Foot Examination (%)

        Numerator: Number of eligible patients with at least one entry for Foot Examination Date (item 26) within the audit period

        Denominator: Number of patients with Type 1 diabetes aged 12+ with a complete year of care in audit period (measure 6)
        """
        kpi_6_total_eligible_query_set, total_eligible_kpi_6 = (
            self._get_total_kpi_6_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = kpi_6_total_eligible_query_set
        total_eligible = total_eligible_kpi_6
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with at least one for Foot Examination Date (item 26) within the audit period
        total_passed_query_set = eligible_patients.filter(
            # Within audit period
            Q(
                visit__foot_examination_observation_date__range=(
                    self.AUDIT_DATE_RANGE
                )
            ),
        )

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    # TODO: confirm calculation definition
    # https://github.com/orgs/rcpch/projects/13/views/1?pane=issue&itemId=79836032
    def calculate_kpi_32_1_health_check_completion_rate(
        self,
    ) -> dict:
        """
        Calculates KPI 32.1: Health check completion rate (%)

        Number of actual health checks over number of expected health checks.
        - Patients = those with T1DM.
        - Patients < 12yo  => expected health checks = 3
            (HbA1c, BMI, Thyroid)
        - patients >= 12yo => expected health checks = 6
            (HbA1c, BMI, Thyroid, BP, Urinary Albumin, Foot Exam)

        TODO: unsure how to calculate [how to find patients with complete year
        of care, do we look across all visits within audit range for a given
        patient to see if eg had hba1c?],
        will catch up with @eatyourpeas to discuss
        """

        # # Get the KPI5&6 querysets
        # kpi_5_total_eligible_query_set, _ = (
        #     self._get_total_kpi_5_eligible_pts_base_query_set_and_total_count()
        # )
        # kpi_6_total_eligible_query_set, _ = (
        #     self._get_total_kpi_6_eligible_pts_base_query_set_and_total_count()
        # )
        # total_eligible = kpi_5_total_eligible_query_set.union(
        #     kpi_6_total_eligible_query_set
        # ).count()
        # total_ineligible = self.total_patients_count - total_eligible

        # # Find patients with ALL KPIS 25,26,27,28,29, 31 PASSING (Apply conditions
        # # to both querysets first, THEN union them)
        # eligibility_conditions = [
        #     # KPI 25
        #     Q(visit__hba1c__isnull=False),
        #     Q(visit__hba1c_date__range=(self.AUDIT_DATE_RANGE)),
        #     # KPI 26
        #     Q(visit__height__isnull=False),
        #     Q(visit__weight__isnull=False),
        #     Q(visit__height_weight_observation_date__range=(self.AUDIT_DATE_RANGE)),
        #     # KPI 27
        #     Q(visit__thyroid_function_date__range=(self.AUDIT_DATE_RANGE)),
        #     # KPI 28
        #     Q(visit__systolic_blood_pressure__isnull=False),
        #     Q(visit__blood_pressure_observation_date__range=(self.AUDIT_DATE_RANGE)),
        #     # KPI 29
        #     Q(visit__albumin_creatinine_ratio__isnull=False),
        #     Q(visit__albumin_creatinine_ratio_date__range=(self.AUDIT_DATE_RANGE)),
        #     # KPI 31
        #     Q(visit__foot_examination_observation_date__range=(self.AUDIT_DATE_RANGE)),
        # ]
        # filtered_kpi_5_eligible = kpi_5_total_eligible_query_set.filter(
        #     *eligibility_conditions
        # )

        # filtered_kpi_6_eligible = kpi_6_total_eligible_query_set.filter(
        #     *eligibility_conditions
        # )

        # # Perform the union after filtering for passing patients
        # eligible_patients_filtered = filtered_kpi_5_eligible.union(
        #     filtered_kpi_6_eligible
        # )
        # total_passed = eligible_patients_filtered.count()
        # total_failed = total_eligible - total_passed

        # return KPIResult(
        #     total_eligible=total_eligible,
        #     total_ineligible=total_ineligible,
        #     total_passed=total_passed,
        #     total_failed=total_failed,
        # )

    def calculate_kpi_33_hba1c_4plus(
        self,
    ) -> dict:
        """
        Calculates KPI 32: HbA1c 4+ (%)

        Numerator: Number of eligible patients with at least four entries for HbA1c value (item 17) with an observation date (item 19) within the audit period

        Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
        """
        kpi_5_total_eligible_query_set, total_eligible_kpi_5 = (
            self._get_total_kpi_5_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = kpi_5_total_eligible_query_set
        total_eligible = total_eligible_kpi_5
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with at least one valid entry for ht & wt within audit period
        total_passed_query_set = eligible_patients.filter(
            Q(visit__height__isnull=False),
            Q(visit__weight__isnull=False),
            # Within audit period
            Q(
                visit__height_weight_observation_date__range=(
                    self.AUDIT_DATE_RANGE
                )
            ),
        )

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def _get_total_kpi_1_eligible_pts_base_query_set_and_total_count(
        self,
    ) -> Tuple[QuerySet, int]:
        """Enables reuse of the base query set for KPI 1

        If running calculation methods in order, this attribute will be set in calculate_kpi_1_total_eligible().

        If running another kpi calculation standalone, need to run that method first to have the attribute set.

        Returns:
            QuerySet: Base query set of eligible patients for KPI 1
            int: base query set count of total eligible patients for KPI 1
        """

        if not hasattr(self, "total_kpi_1_eligible_pts_base_query_set"):
            self.calculate_kpi_1_total_eligible()

        return (
            self.total_kpi_1_eligible_pts_base_query_set,
            self.kpi_1_total_eligible,
        )

    def _get_total_kpi_5_eligible_pts_base_query_set_and_total_count(
        self,
    ) -> Tuple[QuerySet, int]:
        """Enables reuse of the base query set for KPI 5

        If running calculation methods in order, this attribute will be set in calculate_kpi_5_total_t1dm_complete_year().

        If running another kpi calculation standalone, need to run that method first to have the attribute set.

        Returns:
            QuerySet: Base query set of eligible patients for KPI 5
            int: base query set count of total eligible patients for KPI 5
        """

        if not hasattr(self, "total_kpi_1_eligible_pts_base_query_set"):
            self.calculate_kpi_5_total_t1dm_complete_year()

        return (
            self.total_kpi_5_eligible_pts_base_query_set,
            self.kpi_5_total_eligible,
        )

    def _get_total_kpi_6_eligible_pts_base_query_set_and_total_count(
        self,
    ) -> Tuple[QuerySet, int]:
        """Enables reuse of the base query set for KPI 6

        If running calculation methods in order, this attribute will be set in calculate_kpi_6_total_t1dm_complete_year_gte_12yo().

        If running another kpi calculation standalone, need to run that method first to have the attribute set.

        Returns:
            QuerySet: Base query set of eligible patients for KPI 6
            int: base query set count of total eligible patients for KPI 6
        """

        if not hasattr(self, "total_kpi_1_eligible_pts_base_query_set"):
            self.calculate_kpi_6_total_t1dm_complete_year_gte_12yo()

        return (
            self.total_kpi_6_eligible_pts_base_query_set,
            self.kpi_6_total_eligible,
        )


# WIP simply return KPI Agg result for given PDU
class KPIAggregationForPDU(TemplateView):

    template_name = "kpi_aggregations.html"

    def get(self, request, *args, **kwargs):

        pz_code = kwargs.get("pz_code", None)

        start_time = time.time()  # Record the start time for calc
        aggregated_data = CalculateKPIS(
            pz_code=pz_code
        ).calculate_kpis_for_patients()
        end_time = time.time()  # Record the end time
        calculation_time = round(
            (end_time - start_time) * 1000, 2
        )  # Calculate the time taken in milliseconds, rounded to 2dp

        # Add to context
        aggregated_data["calculation_time"] = calculation_time

        return render(request, self.template_name, context=aggregated_data)
