"""Views for KPIs calculations
"""

import logging
import time
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime, timedelta

# Python imports
from decimal import Decimal
from pprint import pformat
from typing import Tuple, Union

from dateutil.relativedelta import relativedelta

# Django imports
from django.apps import apps
from django.db.models import (
    Avg,
    Case,
    Count,
    Exists,
    F,
    Func,
    IntegerField,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    Sum,
    When,
)
from django.shortcuts import render
from django.views.generic import TemplateView

# NPDA Imports
from project.constants.albuminuria_stage import ALBUMINURIA_STAGES
from project.constants.diabetes_types import DIABETES_TYPES
from project.constants.hospital_admission_reasons import HOSPITAL_ADMISSION_REASONS
from project.constants.retinal_screening_results import RETINAL_SCREENING_RESULTS
from project.constants.smoking_status import SMOKING_STATUS
from project.constants.types.kpi_types import KPICalculationsObject, KPIResult
from project.constants.yes_no_unknown import YES_NO_UNKNOWN
from project.npda.general_functions import get_audit_period_for_date
from project.npda.models import Patient, Visit


# Logging
logger = logging.getLogger(__name__)


class CalculateKPIS:
    """
    Calculates KPIs for a given PZ code
    """

    def __init__(
        self, pz_codes: list[str], calculation_date: date = None, patients=None
    ):
        """Calculates KPIs for given pz_code

        Params:
            * pz_code (str) - PZ code for KPIS
            * calculation_date (date) - used to define start and end date of audit period
            * patients (QuerySet) - optional, used to define patients for KPI calculations: this can be used to calculate KPIs for a subset of patients or an individual patient - if not provided, all patients for the given PZ code will be used
        """
        if not pz_codes or len(pz_codes) == 0:
            raise AttributeError("pz_code must be provided")
        # Set various attributes used in calculations
        self.pz_codes = pz_codes
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
        if patients is None:
            self.patients = Patient.objects.filter(
                paediatric_diabetes_units__paediatric_diabetes_unit__pz_code__in=pz_codes
            ).distinct()
            self.total_patients_count = self.patients.count()
        else:
            self.patients = patients
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

    def title_for_kpi(self, kpi_number: int) -> str:
        """Returns a readable title for a given KPI number"""
        # Hard coding these for simplicty and readability
        kpi_titles = {
            1: "Total number of eligible patients",
            2: "Total number of new diagnoses within the audit period",
            3: "Total number of eligible patients with Type 1 diabetes",
            4: "Number of patients aged 12+ with Type 1 diabetes",
            5: "Total number of patients with T1DM who have completed a year of care",
            6: "Total number of patients with T1DM who have completed a year of care and are aged 12 or older",
            7: "Total number of new diagnoses of T1DM",
            8: "Number of patients who died within audit period",
            9: "Number of patients who transitioned/left service within audit period",
            10: "Total number of coeliacs",
            11: "Number of patients with thyroid disease",
            12: "Number of patients with ketone test equipment",
            13: "Number of patients on one to three injections per day",
            14: "Number of patients on four or more injections per day",
            15: "Number of patients on insulin pump",
            16: "Number of patients on one to three injections plus other medication",
            17: "Number of patients on four or more injections plus other medication",
            18: "Number of patients on insulin pump plus other medication",
            19: "Number of patients on dietary management alone",
            20: "Number of patients on dietary management plus other medication",
            21: "Number of patients on flash glucose monitor",
            22: "Number of patients on real-time CGM with alarms",
            23: "Number of patients on Type 1 real-time CGM with alarms",
            24: "Number of patients on hybrid closed loop system",
            25: "Number of patients with HbA1c",
            26: "Number of patients with BMI",
            27: "Number of patients with thyroid screen",
            28: "Number of patients with blood pressure",
            29: "Number of patients with urinary albumin",
            30: "Number of patients with retinal screening",
            31: "Number of patients with foot examination",
            321: "Care processes completion rate",
            322: "Care processes in patients < 12 years old",
            323: "Care processes in patients ≥ 12 years old",
            33: "Number of patients with 4 or more HbA1c measurements",
            34: "Number of patients offered a psychological assessment",
            35: "Number of patients asked about smoking status",
            36: "Number of patients referred to a smoking cessation service",
            37: "Number of patients offered an additional dietetic appointment",
            38: "Number of patients attending an additional dietetic appointment",
            39: "Number of patients recommended influenza immunisation",
            40: "Number of patients given sick day rules advice",
            41: "Number of patients with coeliac disease screening",
            42: "Number of patients with thyroid disease screening",
            43: "Number of patients with carbohydrate counting education",
            44: "Mean HbA1c",
            45: "Median HbA1c",
            46: "Number of admissions",
            47: "Number of DKA admissions",
            48: "Number of patients requiring additional psychological support",
            49: "Number of patients with albuminuria",
        }

        return kpi_titles.get(kpi_number, "Unknown KPI")

    def _run_kpi_calculation_method(
        self, kpi_method_name: str
    ) -> Union[KPIResult | str]:
        """Will find and run kpi calculation method
        (name schema is calculation_KPI_NAME_MAP_VALUE) if found, else returns
        the string "Not implemented".
        """

        kpi_method = getattr(self, f"calculate_{kpi_method_name}", None)

        # If the method is not implemented, set the value to "Not implemented"
        # and skip
        if kpi_method is None:
            return "Not implemented"

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

        return kpi_result

    def calculate_kpis_for_patients(self) -> KPICalculationsObject:
        """Calculate KPIs 1 - 49 for given self.pz_code and cohort range
        (self.audit_start_date and self.audit_end_date).

        We dynamically set these attributes using names set in self.kpis, done in
        the self._get_kpi_attribute_names method during object init.

        Incrementally build the query, which will be executed in a single
        transaction once a value is evaluated.
        """
        # Init dict to store calc results
        calculated_kpis = {}

        # Standard KPIs (all excluding KPI32)
        kpi_idxs = list(range(1, 32)) + (list(range(33, 50)))
        # Now add kpi32 which has 3 sub kpis
        kpi_idxs.extend([321, 322, 323])
        for i in kpi_idxs:
            # Dynamically get the method name from the kpis_names_map
            kpi_method_name = self.kpis_names_map[i]

            kpi_result = self._run_kpi_calculation_method(kpi_method_name)

            # If calculation_method name not found, kpi_result will be
            # "Not implemented"
            if type(kpi_result) == str:
                calculated_kpis[kpi_method_name] = kpi_result
            else:
                # Each kpi method returns a KPIResult object
                # so we convert it first to a dictionary
                calculated_kpis[kpi_method_name] = asdict(kpi_result)

        # Add in used attributes for calculations
        return_obj = {}
        return_obj["pz_codes"] = self.pz_codes
        return_obj["calculation_datetime"] = datetime.now()
        return_obj["audit_start_date"] = self.audit_start_date
        return_obj["audit_end_date"] = self.audit_end_date
        return_obj["total_patients_count"] = self.total_patients_count

        # Finally, add in the kpis
        return_obj["calculated_kpi_values"] = {}
        for kpi_name, kpi_result in calculated_kpis.items():
            return_obj["calculated_kpi_values"][kpi_name] = kpi_result
            return_obj["calculated_kpi_values"][kpi_name]["kpi_label"] = (
                self.title_for_kpi(int(kpi_name.split("_")[1]))
            )

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
            & Q(date_of_birth__gt=self.audit_start_date - relativedelta(years=25))
        )

        # Count eligible patients and set as attribute
        # to be used in subsequent KPI calculations
        self.kpi_1_total_eligible = self.total_kpi_1_eligible_pts_base_query_set.count()
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

        base_eligible_patients, _ = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )

        # This is same as KPI1 but with an additional filter for diagnosis date
        self.total_kpi_2_eligible_pts_base_query_set = base_eligible_patients.filter(
            Q(diagnosis_date__range=(self.AUDIT_DATE_RANGE))
        )

        # Count eligible patients
        self.kpi_2_total_eligible = self.total_kpi_2_eligible_pts_base_query_set.count()
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
        base_eligible_patients, _ = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = base_eligible_patients.filter(
            # is type 1 diabetes
            Q(diabetes_type=DIABETES_TYPES[0][0])
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

        base_eligible_patients, _ = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = base_eligible_patients.filter(
            # Diagnosis of Type 1 diabetes
            Q(diabetes_type=DIABETES_TYPES[0][0])
            # Age 12 and above years at the start of the audit period
            & Q(date_of_birth__lte=self.audit_start_date - relativedelta(years=12))
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
        )

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

        base_eligible_patients = eligible_patients_exclusions.filter(
            # Valid attributes
            Q(nhs_number__isnull=False)
            & Q(date_of_birth__isnull=False)
            # Age 12 and above at the start of the audit period
            & Q(date_of_birth__lte=self.audit_start_date - relativedelta(years=12))
            # Diagnosis of Type 1 diabetes
            & Q(diabetes_type=DIABETES_TYPES[0][0])
        )

        # Find patients with at least one observation within the audit period
        # this requires checking for a date in any of the Visits for a given
        # patient
        valid_visit_subquery = Visit.objects.filter(
            Q(
                Q(height_weight_observation_date__range=(self.AUDIT_DATE_RANGE))
                | Q(hba1c_date__range=(self.AUDIT_DATE_RANGE))
                | Q(blood_pressure_observation_date__range=(self.AUDIT_DATE_RANGE))
                | Q(foot_examination_observation_date__range=(self.AUDIT_DATE_RANGE))
                | Q(retinal_screening_observation_date__range=(self.AUDIT_DATE_RANGE))
                | Q(albumin_creatinine_ratio_date__range=(self.AUDIT_DATE_RANGE))
                | Q(total_cholesterol_date__range=(self.AUDIT_DATE_RANGE))
                | Q(thyroid_function_date__range=(self.AUDIT_DATE_RANGE))
                | Q(coeliac_screen_date__range=(self.AUDIT_DATE_RANGE))
                | Q(
                    psychological_screening_assessment_date__range=(
                        self.AUDIT_DATE_RANGE
                    )
                )
            ),
            patient=OuterRef("pk"),
            visit_date__range=self.AUDIT_DATE_RANGE,
        )

        # Check any observation across all visits
        eligible_pts_annotated_kpi_6_visits = base_eligible_patients.annotate(
            valid_kpi_6_visits=Exists(valid_visit_subquery)
        )

        eligible_patients = eligible_pts_annotated_kpi_6_visits.filter(
            valid_kpi_6_visits__gte=1
        )

        # Count eligible patients
        total_eligible = eligible_patients.count()

        # We reuse this as a base query set for subsequent KPIs so set
        # as an attribute
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

        # total_kpi_1_eligible_pts_base_query_set is slightly different
        # (additionally specifies visit date). So we need to make a new
        # query set
        eligible_patients = self.patients.filter(
            # Valid attributes
            Q(nhs_number__isnull=False)
            & Q(date_of_birth__isnull=False)
            # * Age < 25y years at the start of the audit period
            & Q(date_of_birth__gt=self.audit_start_date - relativedelta(years=25))
            # Diagnosis of Type 1 diabetes
            & Q(diabetes_type=DIABETES_TYPES[0][0])
            & Q(diagnosis_date__range=self.AUDIT_DATE_RANGE)
            & (
                # an observation within the audit period
                # this requires checking for a date in any of the Visit model's
                # observation fields (found simply by searching for date fields
                # with the word 'observation' in the field verbose_name)
                Q(visit__height_weight_observation_date__range=(self.AUDIT_DATE_RANGE))
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
                | Q(visit__albumin_creatinine_ratio_date__range=(self.AUDIT_DATE_RANGE))
                | Q(visit__total_cholesterol_date__range=(self.AUDIT_DATE_RANGE))
                | Q(visit__thyroid_function_date__range=(self.AUDIT_DATE_RANGE))
                | Q(visit__coeliac_screen_date__range=(self.AUDIT_DATE_RANGE))
                | Q(
                    visit__psychological_screening_assessment_date__range=(
                        self.AUDIT_DATE_RANGE
                    )
                )
            )
        )

        # Count eligible patients
        total_eligible = eligible_patients.count()

        # In case we need to use this as a base query set for subsequent KPIs
        self.total_kpi_7_eligible_pts_base_query_set = eligible_patients
        self.kpi_7_total_eligible = total_eligible

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
        base_eligible_patients, _ = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = base_eligible_patients.filter(
            # Date of death within the audit period"
            Q(death_date__range=(self.AUDIT_DATE_RANGE))
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

    def calculate_kpi_9_total_service_transitions(self) -> dict:
        """
        Calculates KPI 9: Number of patients who transitioned/left service within audit period

        Number of eligible patients (measure 1) with
        * a leaving date in the audit period
        """
        base_eligible_patients, _ = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = base_eligible_patients.filter(
            # a leaving date in the audit period
            Q(
                paediatric_diabetes_units__date_leaving_service__range=(
                    self.AUDIT_DATE_RANGE
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
        base_query_set, _ = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )
        eligible_patients = base_query_set.filter(
            Q(
                id__in=Subquery(
                    Patient.objects.filter(visit__in=latest_visit_subquery).values("id")
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
        base_query_set, _ = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )
        eligible_patients = base_query_set.filter(
            Q(
                id__in=Subquery(
                    Patient.objects.filter(visit__in=latest_visit_subquery).values("id")
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
            Visit.objects.filter(patient=OuterRef("pk"), ketone_meter_training=1)
            .order_by("-visit_date")
            .values("pk")[:1]
        )

        # Filter the Patient queryset based on the subquery
        base_query_set, _ = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )
        eligible_patients = base_query_set.filter(
            Q(
                id__in=Subquery(
                    Patient.objects.filter(visit__in=latest_visit_subquery).values("id")
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
        eligible_patients, total_eligible = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )

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
                    Patient.objects.filter(visit__in=latest_visit_subquery).values("id")
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
        eligible_patients, total_eligible = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )

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
                    Patient.objects.filter(visit__in=latest_visit_subquery).values("id")
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
        eligible_patients, total_eligible = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )

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
                    Patient.objects.filter(visit__in=latest_visit_subquery).values("id")
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
        eligible_patients, total_eligible = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )

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
                    Patient.objects.filter(visit__in=latest_visit_subquery).values("id")
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
        eligible_patients, total_eligible = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )
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
                    Patient.objects.filter(visit__in=latest_visit_subquery).values("id")
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
        eligible_patients, total_eligible = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )
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
                    Patient.objects.filter(visit__in=latest_visit_subquery).values("id")
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
        eligible_patients, total_eligible = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )
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
                    Patient.objects.filter(visit__in=latest_visit_subquery).values("id")
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
        eligible_patients, total_eligible = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )
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
                    Patient.objects.filter(visit__in=latest_visit_subquery).values("id")
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
        eligible_patients, total_eligible = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )
        total_ineligible = self.total_patients_count - total_eligible

        # Define the subquery to find the latest visit where blood glucose monitoring (item 22) is either 2 = Flash glucose monitor or 3 = Modified flash glucose monitor (e.g. with MiaoMiao, Blucon etc.)
        latest_visit_subquery = (
            Visit.objects.filter(patient=OuterRef("pk"), glucose_monitoring__in=[2, 3])
            .order_by("-visit_date")
            .values("pk")[:1]
        )
        # Filter the Patient queryset based on the subquery
        total_passed = eligible_patients.filter(
            Q(
                id__in=Subquery(
                    Patient.objects.filter(visit__in=latest_visit_subquery).values("id")
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
        eligible_patients, total_eligible = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )
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
                    Patient.objects.filter(visit__in=latest_visit_subquery).values("id")
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
        eligible_patients, total_eligible = (
            self._get_total_kpi_2_eligible_pts_base_query_set_and_total_count()
        )

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
                    Patient.objects.filter(visit__in=latest_visit_subquery).values("id")
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
        eligible_patients_kpi_24 = total_kpi_1_eligible_pts_base_query_set.filter(
            Q(
                id__in=Subquery(
                    Patient.objects.filter(
                        visit__in=eligible_kpi_24_latest_visit_subquery
                    ).values("id")
                )
            )
        )
        total_eligible_kpi_24 = eligible_patients_kpi_24.count()

        # So ineligible patients are
        #   patients already ineligible for KPI 1
        #   PLUS
        #   the subset of total_kpi_1_eligible_pts_base_query_set
        #   who are ineligible for kpi24 (not on an insulin pump or insulin pump therapy)
        total_ineligible = (self.total_patients_count - total_eligible_kpi_1) + (
            total_eligible_kpi_1 - total_eligible_kpi_24
        )

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
            Q(visit__height_weight_observation_date__range=(self.AUDIT_DATE_RANGE)),
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
            Q(visit__blood_pressure_observation_date__range=(self.AUDIT_DATE_RANGE)),
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
            Q(visit__albumin_creatinine_ratio_date__range=(self.AUDIT_DATE_RANGE)),
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
            Q(visit__retinal_screening_observation_date__range=(self.AUDIT_DATE_RANGE)),
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
            Q(visit__foot_examination_observation_date__range=(self.AUDIT_DATE_RANGE)),
        )

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_32_1_health_check_completion_rate(
        self,
    ) -> dict:
        """
        Calculates KPI 32.1: Health check completion rate (%)
        Number of actual health checks over number of expected health checks.

        Numerator: health checks given
        - Patients = those with T1DM.
        - Patients < 12yo  => expected health checks = 3
            (HbA1c, BMI, Thyroid)
        - patients >= 12yo => expected health checks = 6
            (HbA1c, BMI, Thyroid, BP, Urinary Albumin, Foot Exam)

        Denominator: Number of expected health checks
            - 3 for CYP <12 years with T1D
            - 6 for CYP >= 12 years with T1D

        NOTE: KPIResult(
            total_eligible = total expected health checks,
            total_passed = total actual health checks,
            total_failed = total expected health checks - total actual health checks
            total_ineligible = ineligible PATIENTS
        )
        """

        # Get the eligible patients
        base_eligible_query_set, base_total_eligible = (
            # Pts with T1DM and a complete year of care
            self._get_total_kpi_5_eligible_pts_base_query_set_and_total_count()
        )
        total_ineligible = self.total_patients_count - base_total_eligible

        # Separate the patients into those < 12yo and those >= 12yo
        eligible_patients_lt_12yo = self._get_eligible_pts_measure_5_lt_12yo()
        eligible_patients_gte_12yo = self._get_eligible_pts_measure_5_gte_12yo()

        # Count health checks for patients < 12yo
        # Involves looking at all their Visits, finding if at least 1 of each
        # of the 3 health checks was done (= 1), and then summing this
        hba1c_subquery_lt_12yo = Visit.objects.filter(
            patient=OuterRef("pk"),
            hba1c__isnull=False,
            hba1c_date__range=self.AUDIT_DATE_RANGE,
        )
        bmi_subquery_lt_12yo = Visit.objects.filter(
            patient=OuterRef("pk"),
            height__isnull=False,
            weight__isnull=False,
            height_weight_observation_date__range=self.AUDIT_DATE_RANGE,
        )
        thyroid_subquery_lt_12yo = Visit.objects.filter(
            patient=OuterRef("pk"),
            thyroid_function_date__range=self.AUDIT_DATE_RANGE,
        )

        # Annotate each check individually and convert True to 1, False to 0
        annotated_eligible_pts_lt_12yo = eligible_patients_lt_12yo.annotate(
            hba1c_check=Case(
                When(Exists(hba1c_subquery_lt_12yo), then=1),
                default=0,
                output_field=IntegerField(),
            ),
            bmi_check=Case(
                When(Exists(bmi_subquery_lt_12yo), then=1),
                default=0,
                output_field=IntegerField(),
            ),
            thyroid_check=Case(
                When(Exists(thyroid_subquery_lt_12yo), then=1),
                default=0,
                output_field=IntegerField(),
            ),
        )

        # Annotate each check count and sum them up
        actual_health_checks_lt_12yo = annotated_eligible_pts_lt_12yo.aggregate(
            total_hba1c_checks=Sum("hba1c_check"),
            total_bmi_checks=Sum("bmi_check"),
            total_thyroid_checks=Sum("thyroid_check"),
        )

        # Sum the counts to get the total health checks
        total_health_checks_lt_12yo = sum(
            actual_health_checks_lt_12yo.get(key) or 0
            for key in [
                "total_hba1c_checks",
                "total_bmi_checks",
                "total_thyroid_checks",
            ]
        )

        # Repeat the process for patients >= 12yo

        # Count health checks for patients >= 12yo
        # Involves looking at all their Visits, finding if at least 1 of each
        # of the 6 health checks was done (= 1), and then summing this
        hba1c_subquery_gte_12yo = Visit.objects.filter(
            patient=OuterRef("pk"),
            hba1c__isnull=False,
            hba1c_date__range=self.AUDIT_DATE_RANGE,
        )
        bmi_subquery_gte_12yo = Visit.objects.filter(
            patient=OuterRef("pk"),
            height__isnull=False,
            weight__isnull=False,
            height_weight_observation_date__range=self.AUDIT_DATE_RANGE,
        )
        thyroid_subquery_gte_12yo = Visit.objects.filter(
            patient=OuterRef("pk"),
            thyroid_function_date__range=self.AUDIT_DATE_RANGE,
        )
        bp_subquery_gte_12yo = Visit.objects.filter(
            patient=OuterRef("pk"),
            systolic_blood_pressure__isnull=False,
            blood_pressure_observation_date__range=self.AUDIT_DATE_RANGE,
        )
        urinary_albumin_subquery_gte_12yo = Visit.objects.filter(
            patient=OuterRef("pk"),
            albumin_creatinine_ratio__isnull=False,
            albumin_creatinine_ratio_date__range=self.AUDIT_DATE_RANGE,
        )
        foot_exam_subquery_gte_12yo = Visit.objects.filter(
            patient=OuterRef("pk"),
            foot_examination_observation_date__range=self.AUDIT_DATE_RANGE,
        )

        # Annotate each check individually and convert True to 1, False to 0
        annotated_eligible_pts_gte_12yo = eligible_patients_gte_12yo.annotate(
            hba1c_check=Case(
                When(Exists(hba1c_subquery_gte_12yo), then=1),
                default=0,
                output_field=IntegerField(),
            ),
            bmi_check=Case(
                When(Exists(bmi_subquery_gte_12yo), then=1),
                default=0,
                output_field=IntegerField(),
            ),
            thyroid_check=Case(
                When(Exists(thyroid_subquery_gte_12yo), then=1),
                default=0,
                output_field=IntegerField(),
            ),
            bp_check=Case(
                When(Exists(bp_subquery_gte_12yo), then=1),
                default=0,
                output_field=IntegerField(),
            ),
            urinary_albumin_check=Case(
                When(Exists(urinary_albumin_subquery_gte_12yo), then=1),
                default=0,
                output_field=IntegerField(),
            ),
            foot_exam_check=Case(
                When(Exists(foot_exam_subquery_gte_12yo), then=1),
                default=0,
                output_field=IntegerField(),
            ),
        )

        # Annotate each check count and sum them up
        actual_health_checks_gte_12yo = annotated_eligible_pts_gte_12yo.aggregate(
            total_hba1c_checks=Sum("hba1c_check"),
            total_bmi_checks=Sum("bmi_check"),
            total_thyroid_checks=Sum("thyroid_check"),
            total_bp_checks=Sum("bp_check"),
            total_urinary_albumin_checks=Sum("urinary_albumin_check"),
            total_foot_exam_checks=Sum("foot_exam_check"),
        )

        # Sum the counts to get the total health checks
        total_health_checks_gte_12yo = sum(
            actual_health_checks_gte_12yo.get(key) or 0
            for key in [
                "total_hba1c_checks",
                "total_bmi_checks",
                "total_thyroid_checks",
                "total_bp_checks",
                "total_urinary_albumin_checks",
                "total_foot_exam_checks",
            ]
        )

        actual_health_checks_overall = (
            total_health_checks_lt_12yo + total_health_checks_gte_12yo
        )

        expected_total_health_checks = (
            eligible_patients_lt_12yo.count() * 3
            + eligible_patients_gte_12yo.count() * 6
        )

        return KPIResult(
            total_eligible=expected_total_health_checks,
            total_ineligible=total_ineligible,
            total_passed=actual_health_checks_overall,
            total_failed=expected_total_health_checks - actual_health_checks_overall,
        )

    def calculate_kpi_32_2_health_check_lt_12yo(self) -> dict:
        """
        Calculates KPI 32.2: Health Checks (Less than 12 years)

        Numerator: number of CYP with T1D under 12 years with all three health checks (HbA1c, BMI, Thyroid)

        Denominator:  number of CYP with T1D under 12 years
        """
        # Get the eligible patients
        eligible_patients = self._get_eligible_pts_measure_5_lt_12yo()
        total_eligible = eligible_patients.count()
        total_ineligible = self.total_patients_count - total_eligible

        # Count health checks for patients < 12yo
        # Involves looking at all their Visits, finding if at least 1 of each
        # of the 3 health checks was done (= 1), and then summing this if all
        # 3 checks are done
        hba1c_subquery = Visit.objects.filter(
            patient=OuterRef("pk"),
            hba1c__isnull=False,
            hba1c_date__range=self.AUDIT_DATE_RANGE,
        )
        bmi_subquery = Visit.objects.filter(
            patient=OuterRef("pk"),
            height__isnull=False,
            weight__isnull=False,
            height_weight_observation_date__range=self.AUDIT_DATE_RANGE,
        )
        thyroid_subquery = Visit.objects.filter(
            patient=OuterRef("pk"),
            thyroid_function_date__range=self.AUDIT_DATE_RANGE,
        )

        # Annotate each check individually and convert True to 1, False to 0
        annotated_eligible_pts = eligible_patients.annotate(
            hba1c_check=Case(
                When(Exists(hba1c_subquery), then=1),
                default=0,
                output_field=IntegerField(),
            ),
            bmi_check=Case(
                When(Exists(bmi_subquery), then=1),
                default=0,
                output_field=IntegerField(),
            ),
            thyroid_check=Case(
                When(Exists(thyroid_subquery), then=1),
                default=0,
                output_field=IntegerField(),
            ),
            all_3_hcs_completed=Case(
                When(
                    Q(hba1c_check=1) & Q(bmi_check=1) & Q(thyroid_check=1),
                    then=1,
                ),
                default=0,
                output_field=IntegerField(),
            ),
        )

        total_passed = (
            annotated_eligible_pts.aggregate(
                total_pts_all_hcs_completed=Sum("all_3_hcs_completed")
            ).get("total_pts_all_hcs_completed")
            or 0
        )

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_eligible - total_passed,
        )

    def calculate_kpi_32_3_health_check_gte_12yo(self) -> dict:
        """
        Calculates KPI 32.3: Health Checks (12 years and over)

        Numerator:  Number of CYP with T1D aged 12 years and over with all six
        health checks (HbA1c, BMI, Thyroid, BP, Urinary Albumin, Foot Exam)

        Denominator:  Number of CYP with T1D aged 12 years and over
        """
        # Get the eligible patients
        eligible_patients = self._get_eligible_pts_measure_5_gte_12yo()
        total_eligible = eligible_patients.count()
        total_ineligible = self.total_patients_count - total_eligible

        # Count health checks for patients >= 12yo
        # Involves looking at all their Visits, finding if at least 1 of each
        # of the 6 health checks was done (= 1), and then summing this if all
        # 6 checks are done
        hba1c_subquery = Visit.objects.filter(
            patient=OuterRef("pk"),
            hba1c__isnull=False,
            hba1c_date__range=self.AUDIT_DATE_RANGE,
        )
        bmi_subquery = Visit.objects.filter(
            patient=OuterRef("pk"),
            height__isnull=False,
            weight__isnull=False,
            height_weight_observation_date__range=self.AUDIT_DATE_RANGE,
        )
        thyroid_subquery = Visit.objects.filter(
            patient=OuterRef("pk"),
            thyroid_function_date__range=self.AUDIT_DATE_RANGE,
        )
        bp_subquery = Visit.objects.filter(
            patient=OuterRef("pk"),
            systolic_blood_pressure__isnull=False,
            blood_pressure_observation_date__range=self.AUDIT_DATE_RANGE,
        )
        urinary_albumin_subquery = Visit.objects.filter(
            patient=OuterRef("pk"),
            albumin_creatinine_ratio__isnull=False,
            albumin_creatinine_ratio_date__range=self.AUDIT_DATE_RANGE,
        )
        foot_exam_subquery = Visit.objects.filter(
            patient=OuterRef("pk"),
            foot_examination_observation_date__range=self.AUDIT_DATE_RANGE,
        )

        # Annotate each check individually and convert True to 1, False to 0
        annotated_eligible_pts = eligible_patients.annotate(
            hba1c_check=Case(
                When(Exists(hba1c_subquery), then=1),
                default=0,
                output_field=IntegerField(),
            ),
            bmi_check=Case(
                When(Exists(bmi_subquery), then=1),
                default=0,
                output_field=IntegerField(),
            ),
            thyroid_check=Case(
                When(Exists(thyroid_subquery), then=1),
                default=0,
                output_field=IntegerField(),
            ),
            bp_check=Case(
                When(Exists(bp_subquery), then=1),
                default=0,
                output_field=IntegerField(),
            ),
            urinary_albumin_check=Case(
                When(Exists(urinary_albumin_subquery), then=1),
                default=0,
                output_field=IntegerField(),
            ),
            foot_exam_check=Case(
                When(Exists(foot_exam_subquery), then=1),
                default=0,
                output_field=IntegerField(),
            ),
            all_6_hcs_completed=Case(
                When(
                    Q(hba1c_check=1)
                    & Q(bmi_check=1)
                    & Q(thyroid_check=1)
                    & Q(bp_check=1)
                    & Q(urinary_albumin_check=1)
                    & Q(foot_exam_check=1),
                    then=1,
                ),
                default=0,
                output_field=IntegerField(),
            ),
        )

        total_passed = (
            annotated_eligible_pts.aggregate(
                total_pts_all_hcs_completed=Sum("all_6_hcs_completed")
            ).get("total_pts_all_hcs_completed")
            or 0
        )

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_eligible - total_passed,
        )

    def _get_eligible_pts_measure_5_lt_12yo(self):
        """
        Returns the eligible patients for measure 5 who are under 12 years old
        """
        if hasattr(self, "eligible_pts_lt_12yo"):
            return self.eligible_pts_lt_12yo

        base_eligible_query_set, _ = (
            self._get_total_kpi_5_eligible_pts_base_query_set_and_total_count()
        )

        self.eligible_patients_lt_12yo = base_eligible_query_set.filter(
            Q(date_of_birth__gt=self.audit_start_date - relativedelta(years=12))
        )

        return self.eligible_patients_lt_12yo

    def _get_eligible_pts_measure_5_gte_12yo(self):
        """
        Returns the eligible patients for measure 5 who are gte 12 years old
        """
        if hasattr(self, "eligible_patients_gte_12yo"):
            return self.eligible_patients_gte_12yo

        base_eligible_query_set, _ = (
            self._get_total_kpi_5_eligible_pts_base_query_set_and_total_count()
        )

        self.eligible_patients_gte_12yo = base_eligible_query_set.filter(
            Q(date_of_birth__lte=self.audit_start_date - relativedelta(years=12))
        )

        return self.eligible_patients_gte_12yo

    def calculate_kpi_33_hba1c_4plus(
        self,
    ) -> dict:
        """
        Calculates KPI 33: HbA1c 4+ (%)

        Numerator: Number of eligible patients with at least four entries for HbA1c value (item 17) with an observation date (item 19) within the audit period

        Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
        """
        kpi_5_total_eligible_query_set, total_eligible_kpi_5 = (
            self._get_total_kpi_5_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = kpi_5_total_eligible_query_set
        total_eligible = total_eligible_kpi_5
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with at least 4 entries for HbA1c value with associated
        # observation date within audit period

        # First get query set of patients with at least 4 valid HbA1c measures
        eligible_pts_annotated_hba1c_visits = eligible_patients.annotate(
            hba1c_valid_visits=Count(
                "visit",
                filter=Q(
                    visit__hba1c__isnull=False,
                    visit__hba1c_date__range=self.AUDIT_DATE_RANGE,
                ),
            )
        )
        total_passed_query_set = eligible_pts_annotated_hba1c_visits.filter(
            hba1c_valid_visits__gte=4
        )

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_34_psychological_assessment(
        self,
    ) -> dict:
        """
        Calculates KPI 34: Psychological assessment (%)

        Numerator: Number of eligible patients with an entry for Psychological Screening Date (item 38) within the audit period

        Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
        """
        kpi_5_total_eligible_query_set, total_eligible_kpi_5 = (
            self._get_total_kpi_5_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = kpi_5_total_eligible_query_set
        total_eligible = total_eligible_kpi_5
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with an entry for Psychological Screening Date
        # (item 38) within the audit period

        # First get query set of patients with at least 1 valid psych screen
        eligible_pts_annotated_psych_screen_visits = eligible_patients.annotate(
            psych_valid_visits=Count(
                "visit",
                filter=Q(
                    visit__psychological_screening_assessment_date__range=self.AUDIT_DATE_RANGE,
                ),
            )
        )
        total_passed_query_set = eligible_pts_annotated_psych_screen_visits.filter(
            psych_valid_visits__gte=1
        )

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_35_smoking_status_screened(
        self,
    ) -> dict:
        """
        Calculates KPI 35: Smoking status screened (%)

        Numerator: Number of eligible patients with at least one entry for Smoking Status (item 40) that is either 1 = Non-smoker or 2 = Curent smoker within the audit period (based on visit date)

        Denominator: Number of patients with Type 1 diabetes aged 12+ with a complete year of care in audit period (measure 6)
        """
        kpi_6_total_eligible_query_set, total_eligible_kpi_6 = (
            self._get_total_kpi_6_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = kpi_6_total_eligible_query_set
        total_eligible = total_eligible_kpi_6
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with a valid entry for Smoking status
        # Get the visits that match the valid smoking status criteria
        valid_smoking_visits = Visit.objects.filter(
            patient=OuterRef("pk"),
            visit_date__range=self.AUDIT_DATE_RANGE,
            smoking_status__in=[SMOKING_STATUS[0][0], SMOKING_STATUS[1][0]],
        )
        eligible_pts_annotated_smoke_screen_visits = eligible_patients.annotate(
            smoke_valid_visits=Exists(
                valid_smoking_visits
            )  # This ensures a boolean check if such visits exist
            # NOTE: spent far too long debugging why this would not work
            # by just using Count() and filter when the patient's first
            # Visit had no smoking status but the second did. Some underlying
            # join issue with the first None meaning no subsequent Visits
            # would be founted. Exists() implementation here solved this.
        )

        total_passed_query_set = eligible_pts_annotated_smoke_screen_visits.filter(
            smoke_valid_visits__gte=1
        )

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_36_referral_to_smoking_cessation_service(
        self,
    ) -> dict:
        """
        Calculates KPI 36: Referral to smoking cessation service (%)

        Numerator: Number of eligible patients with an entry for Date of Smoking Cessation Referral (item 41) within the audit period

        Denominator: Number of patients with Type 1 diabetes aged 12+ with a complete year of care in audit period (measure 6)
        """
        kpi_6_total_eligible_query_set, total_eligible_kpi_6 = (
            self._get_total_kpi_6_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = kpi_6_total_eligible_query_set
        total_eligible = total_eligible_kpi_6
        total_ineligible = self.total_patients_count - total_eligible

        # Get the visits that match the valid Smoking Cessation Referral date
        smoke_cessation_visits = Visit.objects.filter(
            patient=OuterRef("pk"),
            visit_date__range=self.AUDIT_DATE_RANGE,
            smoking_cessation_referral_date__range=self.AUDIT_DATE_RANGE,
        )
        # Find patients with a valid entry for Smoking Cessation Referral
        eligible_pts_annotated_smoke_screen_visits = eligible_patients.annotate(
            smoke_cessation_referral_valid_visits=Exists(smoke_cessation_visits)
        )

        total_passed_query_set = eligible_pts_annotated_smoke_screen_visits.filter(
            smoke_cessation_referral_valid_visits__gte=1
        )

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_37_additional_dietetic_appointment_offered(
        self,
    ) -> dict:
        """
        Calculates KPI 37: Additional dietetic appointment offered (%)

        Numerator: Numer of eligible patients with at least one entry for Additional Dietitian Appointment Offered (item 43) that is 1 = Yes within the audit period (based on visit date)

        Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
        """
        kpi_5_total_eligible_query_set, total_eligible_kpi_5 = (
            self._get_total_kpi_5_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = kpi_5_total_eligible_query_set
        total_eligible = total_eligible_kpi_5
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with at least one entry for Additional Dietitian Appointment Offered (item 43) that is 1 = Yes within the audit period (based on visit date)
        eligible_pts_annotated_dietician_offered_visits = eligible_patients.annotate(
            dietician_offered_valid_visits=Count(
                "visit",
                filter=Q(
                    visit__visit_date__range=self.AUDIT_DATE_RANGE,
                    visit__dietician_additional_appointment_offered=1,
                ),
            )
        )
        total_passed_query_set = eligible_pts_annotated_dietician_offered_visits.filter(
            dietician_offered_valid_visits__gte=1
        )

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_38_patients_attending_additional_dietetic_appointment(
        self,
    ) -> dict:
        """
        Calculates KPI 38: Patients attending additional dietetic appointment (%)

        Numerator: Number of eligible patients with at least one entry for Additional Dietitian Appointment Date (item 44) within the audit year

        Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
        """
        kpi_5_total_eligible_query_set, total_eligible_kpi_5 = (
            self._get_total_kpi_5_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = kpi_5_total_eligible_query_set
        total_eligible = total_eligible_kpi_5
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with at least one entry for Additional Dietitian
        # Appointment Date (item 44) within the audit year
        eligible_pts_annotated_dietician_additional_visits = eligible_patients.annotate(
            dietician_additional_valid_visits=Count(
                "visit",
                filter=Q(
                    visit__visit_date__range=self.AUDIT_DATE_RANGE,
                    visit__dietician_additional_appointment_date__range=self.AUDIT_DATE_RANGE,
                ),
            )
        )
        total_passed_query_set = (
            eligible_pts_annotated_dietician_additional_visits.filter(
                dietician_additional_valid_visits__gte=1
            )
        )

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_39_influenza_immunisation_recommended(
        self,
    ) -> dict:
        """
        Calculates KPI 39: Influenza immunisation recommended (%)

        Numerator: Number of eligible patients with at least one entry for Influzena Immunisation Recommended (item 24) within the audit period

        Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
        """
        kpi_5_total_eligible_query_set, total_eligible_kpi_5 = (
            self._get_total_kpi_5_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = kpi_5_total_eligible_query_set
        total_eligible = total_eligible_kpi_5
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with at least one entry for Influzena Immunisation
        # Recommended (item 24) within the audit period
        eligible_pts_annotated_flu_immunisation_recommended_date_visits = eligible_patients.annotate(
            flu_immunisation_recommended_date_valid_visits=Count(
                "visit",
                filter=Q(
                    visit__visit_date__range=self.AUDIT_DATE_RANGE,
                    visit__flu_immunisation_recommended_date__range=self.AUDIT_DATE_RANGE,
                ),
            )
        )
        total_passed_query_set = (
            eligible_pts_annotated_flu_immunisation_recommended_date_visits.filter(
                flu_immunisation_recommended_date_valid_visits__gte=1
            )
        )

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_40_sick_day_rules_advice(
        self,
    ) -> dict:
        """
        Calculates KPI 40: Sick day rules advice (%)

        Numerator:Number of eligible patients with at least one entry for Sick
        Day Rules (item 47) within the audit period

        Denominator: Total number of eligible patients (measure 1)
        """
        kpi_1_total_eligible_query_set, total_eligible_kpi_1 = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )

        eligible_patients = kpi_1_total_eligible_query_set
        total_eligible = total_eligible_kpi_1
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with at least one entry for Sick
        # Day Rules (item 47) within the audit period
        eligible_pts_annotated_sick_day_rules_visits = eligible_patients.annotate(
            sick_day_rules_valid_visits=Count(
                "visit",
                filter=Q(
                    visit__visit_date__range=self.AUDIT_DATE_RANGE,
                    visit__sick_day_rules_training_date__range=self.AUDIT_DATE_RANGE,
                ),
            )
        )
        total_passed_query_set = eligible_pts_annotated_sick_day_rules_visits.filter(
            sick_day_rules_valid_visits__gte=1
        )

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_41_coeliac_disease_screening(
        self,
    ) -> dict:
        """
        Calculates KPI 41: Coeliac diasease screening (%)

        Numerator: Number of eligible patients with an entry for Coeliac Disease Screening Date (item 36) within 90 days of Date of Diabetes Diagnosis (item 7)

        Denominator: Number of patients with Type 1 diabetes who were diagnosed at least 90 days before the end of the audit period.

        NOTE: denominator is essentially KPI7 (total new T1DM diagnoses) plus
        extra filter for diabetes diagnosis < (AUDIT_END_DATE - 90 DAYS)
        """
        eligible_patients, total_eligible = (
            self._get_total_pts_new_t1dm_diag_90D_before_audit_end_base_query_set_and_total_count()
        )
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with an entry for Coeliac Disease
        # Screening Date (item 36) 90 days before or after diabetes diagnosis
        # date
        eligible_pts_annotated_coeliac_screen_visits = eligible_patients.annotate(
            coeliac_screen_valid_visits=Count(
                "visit",
                # NOTE: relativedelta not supported
                filter=Q(
                    visit__coeliac_screen_date__gte=F("diagnosis_date")
                    - timedelta(days=90),
                    visit__coeliac_screen_date__lte=F("diagnosis_date")
                    + timedelta(days=90),
                ),
            )
        )
        total_passed_query_set = eligible_pts_annotated_coeliac_screen_visits.filter(
            coeliac_screen_valid_visits__gte=1
        )

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_42_thyroid_disease_screening(
        self,
    ) -> dict:
        """
        Calculates KPI 42: Thyroid disaese screening (%)

        Numerator: Number of eligible patients with an entry for Thyroid Function Observation Date (item 34) within 90 days (<= | >=) of Date of Diabetes Diagnosis (item 7)

        Denominator: Number of patients with Type 1 diabetes who were diagnosed at least 90 days before the end of the audit period

        (NOTE: measure 7 AND diabetes diagnosis date < (AUDIT_END_DATE - 90 days))
        """
        eligible_patients, total_eligible = (
            self._get_total_pts_new_t1dm_diag_90D_before_audit_end_base_query_set_and_total_count()
        )
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with an entry for Thyroid Function Observation Date
        # (item 36) 90 days before or after diabetes diagnosis date
        eligible_pts_annotated_thyroid_fn_date_visits = eligible_patients.annotate(
            thyroid_fn_date_valid_visits=Count(
                "visit",
                # NOTE: relativedelta not supported
                filter=Q(
                    visit__thyroid_function_date__gte=F("diagnosis_date")
                    - timedelta(days=90),
                    visit__thyroid_function_date__lte=F("diagnosis_date")
                    + timedelta(days=90),
                ),
            )
        )
        total_passed_query_set = eligible_pts_annotated_thyroid_fn_date_visits.filter(
            thyroid_fn_date_valid_visits__gte=1
        )

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_43_carbohydrate_counting_education(
        self,
    ) -> dict:
        """
        Calculates KPI 43: Carbohydrate counting education (%)

        Numerator: Number of eligible patients with an entry for Carbohydrate
        Counting Education (item 42) within 7 days before or 14 days after the
        Date of Diabetes Diagnosis (item 7)

        Denominator: Number of patients with Type 1 diabetes who were diagnosed
        at least 14 days before the end of the audit period (<= | >=)

        (NOTE: Measure 7 AND diabetes diagnosis date < (AUDIT_END_DATE - 14 days))
        """

        # Eligible patients are measure 7 with
        # diagnosis date < (AUDIT_END_DATE - 14 days)
        base_eligible_patients, _ = (
            self._get_total_kpi_7_eligible_pts_base_query_set_and_total_count()
        )
        eligible_patients = base_eligible_patients.filter(
            diagnosis_date__lt=self.audit_end_date - relativedelta(days=14)
        )
        total_eligible = eligible_patients.count()
        total_ineligible = self.total_patients_count - total_eligible

        # Find visits with an entry for Carbohydrate Counting Education
        # (item 42) within 7 days before or 14 days after the
        # Date of Diabetes Diagnosis (item 7)
        valid_visit_subquery = Visit.objects.filter(
            patient=OuterRef("pk"),
            carbohydrate_counting_level_three_education_date__gte=F(
                "patient__diagnosis_date"
            )
            - timedelta(days=7),
            carbohydrate_counting_level_three_education_date__lte=F(
                "patient__diagnosis_date"
            )
            + timedelta(days=14),
        )

        # Annotate eligible patients with a boolean indicating the existence
        # of a valid Visit. NOTE: doing this because Count has weird behavior
        # if the first Visit has no valid carb date even if second does
        eligible_pts_annotated = eligible_patients.annotate(
            has_valid_visit=Exists(valid_visit_subquery)
        )

        # Filter patients who have at least one valid Visit
        total_passed_query_set = eligible_pts_annotated.filter(has_valid_visit=True)

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_44_mean_hba1c(
        self,
    ) -> dict:
        """
        Calculates KPI 44: Mean HbA1c

        SINGLE NUMBER: Mean of HbA1c measurements (item 17) within the audit
        period, excluding measurements taken within 90 days of diagnosis
        NOTE: The median for each patient is calculated. We then calculate the
        mean of the medians.

        Denominator: Total number of eligible patients (measure 1)

        NOTE: Django does not support Median aggregation function. We can do
        manually.
        """
        eligible_patients, total_eligible = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )
        total_ineligible = self.total_patients_count - total_eligible

        # Calculate median HBa1c for each patient

        # Get the visits that match the valid HbA1c criteria

        # Subquery to filter valid HBA1c values while ensuring visit_date is in
        # the required range
        valid_hba1c_subquery = (
            Visit.objects.filter(
                visit_date__range=self.AUDIT_DATE_RANGE,
                hba1c_date__gte=F("patient__diagnosis_date")
                + timedelta(days=90),  # Ensure HbA1c is taken >90 days after diagnosis
                patient=OuterRef("pk"),
            )
            # Clear any implicit ordering, select only 'hba1c' for calculating
            # the median as getting error with the visit_date field
            .order_by().values("hba1c")
        )

        # Annotate eligible patients with the median HbA1c value
        eligible_pts_annotated = eligible_patients.annotate(
            median_hba1c=Subquery(
                valid_hba1c_subquery.annotate(median_hba1c=Median("hba1c")).values(
                    "median_hba1c"
                )[:1]
            )
        )

        # Calculate the median of the medians and convert to float (as Decimal)
        median_of_median_hba1cs = (
            eligible_pts_annotated.aggregate(
                median_of_median_hba1cs=Avg("median_hba1c")
            ).get("median_of_median_hba1cs")
            or 0
        )

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            # Use passed for storing the value
            total_passed=median_of_median_hba1cs,
            # Failed is not used
            total_failed=-1,
        )

    def calculate_kpi_45_median_hba1c(
        self,
    ) -> dict:
        """
        Calculates KPI 43: Median HbA1c

        SINGLE NUMBER: median of HbA1c measurements (item 17) within the audit
        period, excluding measurements taken within 90 days of diagnosis

        NOTE: The median for each patient is calculated. We then calculate the
        median of the medians.

        Denominator: Total number of eligible patients (measure 1)
        """
        eligible_patients, total_eligible = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )
        total_ineligible = self.total_patients_count - total_eligible

        # Calculate median HBa1c for each patient

        # Get the visits that match the valid HbA1c criteria

        # Subquery to filter valid HBA1c values while ensuring visit_date is in
        # the required range
        valid_hba1c_subquery = (
            Visit.objects.filter(
                visit_date__range=self.AUDIT_DATE_RANGE,
                hba1c_date__gte=F("patient__diagnosis_date")
                + timedelta(days=90),  # Ensure HbA1c is taken >90 days after diagnosis
                patient=OuterRef("pk"),
            )
            # Clear any implicit ordering, select only 'hba1c' for calculating
            # the median as getting error with the visit_date field
            .order_by().values("hba1c")
        )

        # Annotate eligible patients with the median HbA1c value
        eligible_pts_annotated = eligible_patients.annotate(
            median_hba1c=Subquery(
                valid_hba1c_subquery.annotate(median_hba1c=Median("hba1c")).values(
                    "median_hba1c"
                )[:1]
            )
        )

        # Calculate the mean of the medians and convert to float (as Decimal)
        mean_of_median_hba1cs = (
            eligible_pts_annotated.aggregate(
                mean_of_median_hba1cs=Avg("median_hba1c")
            ).get("mean_of_median_hba1cs")
            or 0
        )

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            # Use passed for storing the value
            total_passed=mean_of_median_hba1cs,
            # Failed is not used
            total_failed=-1,
        )

    def calculate_kpi_46_number_of_admissions(
        self,
    ) -> dict:
        """
        Calculates KPI 46: Number of admissions

        Numerator:Total number of admissions with a valid reason for admission
        (item 50) AND with a start date (item 48) OR discharge date (item 49)
        within the audit period
        NOTE: There can be more than one admission per patient, but eliminate
        duplicate entries


        Denominator: Total number of eligible patients (measure 1)
        """
        eligible_patients, total_eligible = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with at least one valid admission
        # Get the visits that match the valid admission criteria
        valid_visit_subquery = Visit.objects.filter(
            # admission start date OR discharge date within audit period
            Q(
                Q(hospital_admission_date__range=self.AUDIT_DATE_RANGE)
                | Q(hospital_discharge_date__range=self.AUDIT_DATE_RANGE)
            ),
            # valid reason for admission
            hospital_admission_reason__in=[
                choice[0] for choice in HOSPITAL_ADMISSION_REASONS
            ],
            patient=OuterRef("pk"),
            visit_date__range=self.AUDIT_DATE_RANGE,
        )

        # Annotate eligible patients with a boolean indicating the existence
        # of a valid Visit. NOTE: doing this because Count has weird behavior
        # if the first Visit has no valid value even if second does
        eligible_pts_annotated = eligible_patients.annotate(
            has_valid_visit=Exists(valid_visit_subquery)
        )

        # Filter patients who have at least one valid Visit
        total_passed_query_set = eligible_pts_annotated.filter(has_valid_visit=True)

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_47_number_of_dka_admissions(
        self,
    ) -> dict:
        """
        Calculates KPI 47: Number of DKA admissions


        Numerator:Total number of admissions with a reason for admission
        (item 50) that is 2 = DKA AND with a start date (item 48) OR
        discharge date (item 49) within the audit period
        NOTE: There can be more than one admission per patient, but eliminate
        duplicate entries

        Denominator: Total number of eligible patients (measure 1)
        """
        eligible_patients, total_eligible = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with at least one valid DKA admission criteria
        # Get the visits that match the valid DKA admission criteria
        valid_visit_subquery = Visit.objects.filter(
            # admission start date OR discharge date within audit period
            Q(
                Q(hospital_admission_date__range=self.AUDIT_DATE_RANGE)
                | Q(hospital_discharge_date__range=self.AUDIT_DATE_RANGE)
            ),
            # DKA reason 2
            hospital_admission_reason=HOSPITAL_ADMISSION_REASONS[1][0],
            patient=OuterRef("pk"),
            visit_date__range=self.AUDIT_DATE_RANGE,
        )

        # Annotate eligible patients with a boolean indicating the existence
        # of a valid Visit. NOTE: doing this because Count has weird behavior
        # if the first Visit has no valid value even if second does
        eligible_pts_annotated = eligible_patients.annotate(
            has_valid_visit=Exists(valid_visit_subquery)
        )

        # Filter patients who have at least one valid Visit
        total_passed_query_set = eligible_pts_annotated.filter(has_valid_visit=True)

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_48_required_additional_psychological_support(
        self,
    ) -> dict:
        """
        Calculates KPI 48: Required additional psychological support

        Numerator:Total number of eligible patients with at least one entry for
        Psychological Support (item 39) that is 1 = Yes within the audit period
        (based on visit date)

        Denominator: Total number of eligible patients (measure 1)
        """
        eligible_patients, total_eligible = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with at least one valid psych support criteria
        # Get the visits that match the valid psych support=1 criteria
        valid_visit_subquery = Visit.objects.filter(
            # required additional psychological support
            psychological_additional_support_status=YES_NO_UNKNOWN[0][0],
            patient=OuterRef("pk"),
            visit_date__range=self.AUDIT_DATE_RANGE,
        )

        # Annotate eligible patients with a boolean indicating the existence
        # of a valid Visit. NOTE: doing this because Count has weird behavior
        # if the first Visit has no valid value even if second does
        eligible_pts_annotated = eligible_patients.annotate(
            has_valid_visit=Exists(valid_visit_subquery)
        )

        # Filter patients who have at least one valid Visit
        total_passed_query_set = eligible_pts_annotated.filter(has_valid_visit=True)

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def calculate_kpi_49_albuminuria_present(
        self,
    ) -> dict:
        """
        Calculates KPI 49: Albuminuria present

        Numerator: Total number of eligible patients whose most recent
        entry for for Albuminuria Stage (item 31) based on observation date
        (item 30) is 2 = Microalbuminuria or 3 = Macroalbuminuria

        Denominator: Total number of eligible patients (measure 1)
        """
        eligible_patients, total_eligible = (
            self._get_total_kpi_1_eligible_pts_base_query_set_and_total_count()
        )
        total_ineligible = self.total_patients_count - total_eligible

        # Find patients with at least one valid albuminuria stage criteria
        # Get the visits that match the valid albuminuria criteria
        valid_visit_subquery = Visit.objects.filter(
            # valid albuminuria stage 2 or 3
            albuminuria_stage__in=[
                ALBUMINURIA_STAGES[1][0],
                ALBUMINURIA_STAGES[2][0],
            ],
            patient=OuterRef("pk"),
            visit_date__range=self.AUDIT_DATE_RANGE,
        )

        # Annotate eligible patients with a boolean indicating the existence
        # of a valid Visit. NOTE: doing this because Count has weird behavior
        # if the first Visit has no valid value even if second does
        eligible_pts_annotated = eligible_patients.annotate(
            has_valid_visit=Exists(valid_visit_subquery)
        )

        # Filter patients who have at least one valid Visit
        total_passed_query_set = eligible_pts_annotated.filter(has_valid_visit=True)

        total_passed = total_passed_query_set.count()
        total_failed = total_eligible - total_passed

        return KPIResult(
            total_eligible=total_eligible,
            total_ineligible=total_ineligible,
            total_passed=total_passed,
            total_failed=total_failed,
        )

    def _debug_helper_print_postcode_and_attrs(self, patient_queryset, *attrs):
        """Helper function to be used with tests which prints out the postcode
        and specified attributes for each patient in the queryset
        """

        logger.debug(f"===QuerySet:{str(patient_queryset)}===")
        logger.debug(f"==={self.AUDIT_DATE_RANGE=}===\n")
        for item in patient_queryset.values("postcode", *attrs):
            logger.debug(f'Patient Name: {item["postcode"]}')
            del item["postcode"]
            logger.debug(pformat(item) + "\n")

        logger.debug(f"====================")

    def _get_total_kpi_1_eligible_pts_base_query_set_and_total_count(
        self,
    ) -> Tuple[QuerySet[Patient], int]:
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

    def _get_total_kpi_2_eligible_pts_base_query_set_and_total_count(
        self,
    ) -> Tuple[QuerySet[Patient], int]:
        """Enables reuse of the base query set for KPI 2

        If running calculation methods in order, this attribute will be set in calculate_kpi_2_total_new_diagnoses().

        If running another kpi calculation standalone, need to run that method first to have the attribute set.

        Returns:
            QuerySet: Base query set of eligible patients for KPI 2
            int: base query set count of total eligible patients for KPI 2
        """

        if not hasattr(self, "total_kpi_2_eligible_pts_base_query_set"):
            self.calculate_kpi_2_total_new_diagnoses()

        return (
            self.total_kpi_2_eligible_pts_base_query_set,
            self.kpi_2_total_eligible,
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

    def _get_total_kpi_7_eligible_pts_base_query_set_and_total_count(
        self,
    ) -> Tuple[QuerySet, int]:
        """Enables reuse of the base query set for KPI 7

        If running calculation methods in order, this attribute will be set in calculate_kpi_7_total_t1dm_complete_year_gte_12yo().

        If running another kpi calculation standalone, need to run that method first to have the attribute set.

        Returns:
            QuerySet: Base query set of eligible patients for KPI 7
            int: base query set count of total eligible patients for KPI 7
        """

        if not hasattr(self, "total_kpi_1_eligible_pts_base_query_set"):
            self.calculate_kpi_7_total_new_diagnoses_t1dm()

        return (
            self.total_kpi_7_eligible_pts_base_query_set,
            self.kpi_7_total_eligible,
        )

    def _get_total_pts_new_t1dm_diag_90D_before_audit_end_base_query_set_and_total_count(
        self,
    ) -> Tuple[QuerySet, int]:
        """Enables reuse of the base query set for denominator in KPIS 41-43
        (patients with new T1DM, diagnosed at least 90 days before audit end
        date).

        Returns:
            QuerySet: Base query set of eligible patients for KPIs 41-43
            int: base query set count of total eligible patients for KPI 41-43

        NOTE: this is essentially KPI 7 plus an extra filter for diagnosis_date
        < 90 days before audit end date
        """

        # This might be run already so check if attribute exists
        if hasattr(self, "t1dm_pts_diagnosed_90D_before_end_base_query_set"):
            return (
                self.t1dm_pts_diagnosed_90D_before_end_base_query_set,
                self.t1dm_pts_diagnosed_90D_before_end_total_eligible,
            )

        # First get new T1DM diagnoses pts
        base_query_set, _ = (
            self._get_total_kpi_7_eligible_pts_base_query_set_and_total_count()
        )

        # Filter for those diagnoses at least 90 days before audit end date
        self.t1dm_pts_diagnosed_90D_before_end_base_query_set = base_query_set.filter(
            diagnosis_date__lt=self.audit_end_date - relativedelta(days=90),
        )
        self.t1dm_pts_diagnosed_90D_before_end_total_eligible = (
            self.t1dm_pts_diagnosed_90D_before_end_base_query_set.count()
        )

        return (
            self.t1dm_pts_diagnosed_90D_before_end_base_query_set,
            self.t1dm_pts_diagnosed_90D_before_end_total_eligible,
        )


# Custom Median function for PostgreSQL
class Median(Func):
    function = "percentile_cont"
    template = "%(function)s(0.5) WITHIN GROUP (ORDER BY %(expressions)s)"


def queryset_median_value(queryset: QuerySet, column_name: str):
    """Calculates the median value of a given column_name:str in a queryset

    Median is not a SQL aggregate function so we have to calculate it manually

    Thanks https://stackoverflow.com/questions/942620/missing-median-aggregate-function-in-django.
    """
    count = queryset.count()
    values = queryset.values_list(column_name, flat=True).order_by(column_name)
    if count % 2 == 1:
        return values[int(round(count / 2))]
    else:
        return sum(values[count / 2 - 1 : count / 2 + 1]) / Decimal(2.0)


# WIP simply return KPI Agg result for given PDU
class KPIAggregationForPDU(TemplateView):

    template_name = "kpi_aggregations.html"

    def get(self, request, *args, **kwargs):

        pz_code = kwargs.get("pz_code", None)

        start_time = time.time()  # Record the start time for calc
        aggregated_data = CalculateKPIS(pz_code=pz_code).calculate_kpis_for_patients()
        end_time = time.time()  # Record the end time
        calculation_time = round(
            (end_time - start_time) * 1000, 2
        )  # Calculate the time taken in milliseconds, rounded to 2dp

        # Add to context
        aggregated_data["calculation_time"] = calculation_time

        return render(request, self.template_name, context=aggregated_data)
