"""Views for KPIs"""

# Python imports
from dataclasses import dataclass, is_dataclass
from dataclasses import asdict
from datetime import date
import logging
from dateutil.relativedelta import relativedelta

# Django imports
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db.models import Q, OuterRef, Subquery

# NPDA Imports
from project.constants.diabetes_types import DIABETES_TYPES
from project.npda.models import Patient
from project.npda.general_functions import get_audit_period_for_date
from project.npda.general_functions.kpis_calculations import kpi_2_total_new_diagnoses
from project.npda.general_functions.kpis_calculations import kpi_3_total_t1dm
from project.npda.general_functions.kpis_calculations import kpi_4_total_t1dm_gte_12yo
from project.npda.general_functions.kpis_calculations import (
    kpi_5_total_t1dm_complete_year,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_6_total_t1dm_complete_year_gte_12yo,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_7_total_new_diagnoses_t1dm,
)
from project.npda.general_functions.kpis_calculations import kpi_8_total_deaths
from project.npda.general_functions.kpis_calculations import (
    kpi_9_total_service_transitions,
)
from project.npda.general_functions.kpis_calculations import kpi_10_total_coeliacs
from project.npda.general_functions.kpis_calculations import kpi_11_total_thyroids
from project.npda.general_functions.kpis_calculations import (
    kpi_12_total_ketone_test_equipment,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_13_one_to_three_injections_per_day,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_14_four_or_more_injections_per_day,
)
from project.npda.general_functions.kpis_calculations import kpi_15_insulin_pump
from project.npda.general_functions.kpis_calculations import (
    kpi_16_one_to_three_injections_plus_other_medication,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_17_four_or_more_injections_plus_other_medication,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_18_insulin_pump_plus_other_medication,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_19_dietary_management_alone,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_20_dietary_management_plus_other_medication,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_21_flash_glucose_monitor,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_22_real_time_cgm_with_alarms,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_23_type1_real_time_cgm_with_alarms,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_24_hybrid_closed_loop_system,
)
from project.npda.general_functions.kpis_calculations import kpi_25_hba1c
from project.npda.general_functions.kpis_calculations import kpi_26_bmi
from project.npda.general_functions.kpis_calculations import kpi_27_thyroid_screen
from project.npda.general_functions.kpis_calculations import kpi_28_blood_pressure
from project.npda.general_functions.kpis_calculations import kpi_29_urinary_albumin
from project.npda.general_functions.kpis_calculations import kpi_30_retinal_screening
from project.npda.general_functions.kpis_calculations import kpi_31_foot_examination
from project.npda.general_functions.kpis_calculations import (
    kpi_32_health_check_completion_rate,
)
from project.npda.general_functions.kpis_calculations import kpi_33_hba1c_4plus
from project.npda.general_functions.kpis_calculations import (
    kpi_34_psychological_assessment,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_35_smoking_status_screened,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_36_referral_to_smoking_cessation_service,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_37_additional_dietetic_appointment_offered,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_38_patients_attending_additional_dietetic_appointment,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_39_influenza_immunisation_recommended,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_40_sick_day_rules_advice,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_41_coeliac_disease_screening,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_42_thyroid_disease_screening,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_43_carbohydrate_counting_education,
)
from project.npda.general_functions.kpis_calculations import kpi_44_mean_hba1c
from project.npda.general_functions.kpis_calculations import kpi_45_median_hba1c
from project.npda.general_functions.kpis_calculations import kpi_46_number_of_admissions
from project.npda.general_functions.kpis_calculations import (
    kpi_47_number_of_dka_admissions,
)
from project.npda.general_functions.kpis_calculations import (
    kpi_48_required_additional_psychological_support,
)
from project.npda.general_functions.kpis_calculations import kpi_49_albuminuria_present
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
            32: "kpi_32_health_check_completion_rate",
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

        # Calculate KPIs 1 - 12, used as denominators for subsequent KPIs
        for i in range(1, 7):
            kpi_method_name = self.kpis_names_map[i]
            kpi_method = getattr(self, f"calculate_{kpi_method_name}")
            kpi_result = kpi_method()

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

        # Calculate remaining KPIs (13-49)
        # for i in range(13, 50):
        #     kpi_method_name = self.kpis[i]
        #     kpi_method = getattr(self, f"calculate_{kpi_method_name}")
        #     calculated_kpis[kpi_method_name] = kpi_method(calculated_kpis)

        # Add in used attributes for calculations
        return_obj = {}
        return_obj["pz_code"] = self.pz_code
        return_obj["calculation_date"] = self.calculation_date
        return_obj["audit_start_date"] = self.audit_start_date
        return_obj["audit_end_date"] = self.audit_end_date

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
            & Q(date_of_birth__gt=self.audit_start_date - relativedelta(years=25))
        )

        eligible_patients = self.total_kpi_1_eligible_pts_base_query_set.distinct()
        total_eligible = eligible_patients.count()

        # Count eligible patients and set as attribute
        # to be used in subsequent KPI calculations
        total_eligible = eligible_patients.count()

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

        # This is same as KPI1 but with an additional filter for diagnosis date
        eligible_patients = self.total_kpi_1_eligible_pts_base_query_set.filter(
            Q(diagnosis_date__range=(self.AUDIT_DATE_RANGE))
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
            & Q(date_of_birth__lte=self.audit_start_date - relativedelta(years=12))
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
        eligible_patients = self.total_kpi_1_eligible_pts_base_query_set.exclude(
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
            & Q(date_of_birth__lte=self.audit_start_date - relativedelta(years=12))
            # Diagnosis of Type 1 diabetes
            & Q(diabetes_type=DIABETES_TYPES[0][0])
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
        eligible_patients = self.total_kpi_1_eligible_pts_base_query_set.filter(
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
        eligible_patients = self.total_kpi_1_eligible_pts_base_query_set.filter(
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
        eligible_patients = self.total_kpi_1_eligible_pts_base_query_set.filter(
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

    def calculate_kpi_numerator_13(self) -> dict:
        """
        Calculates KPI 13: Total number of patients on 1-3 injections per day
        """
        return kpi_13_one_to_three_injections_per_day(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_14(self) -> dict:
        """
        Calculates KPI 14: Total number of patients on 4 or more injections per day
        """
        return kpi_14_four_or_more_injections_per_day(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_15(self) -> dict:
        """
        Calculates KPI 15: Total number of patients on insulin pump
        """
        return kpi_15_insulin_pump(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_16(self) -> dict:
        """
        Calculates KPI 16: Total number of patients on 1-3 injections per day plus other medication
        """
        return kpi_16_one_to_three_injections_plus_other_medication(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_17(self) -> dict:
        """
        Calculates KPI 17: Total number of patients on 4 or more injections per day plus other medication
        """
        return kpi_17_four_or_more_injections_plus_other_medication(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_18(self) -> dict:
        """
        Calculates KPI 18: Total number of patients on insulin pump plus other medication
        """
        return kpi_18_insulin_pump_plus_other_medication(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_19(self) -> dict:
        """
        Calculates KPI 19: Total number of patients on dietary management alone
        """
        return kpi_19_dietary_management_alone(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_20(self) -> dict:
        """
        Calculates KPI 20: Total number of patients on dietary management plus other medication
        """
        return kpi_20_dietary_management_plus_other_medication(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_21(self) -> dict:
        """
        Calculates KPI 21: Total number of patients on flash glucose monitor
        """
        return kpi_21_flash_glucose_monitor(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_22(self) -> dict:
        """
        Calculates KPI 22: Total number of patients on real time CGM with alarms
        """
        return kpi_22_real_time_cgm_with_alarms(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_23(self) -> dict:
        """
        Calculates KPI 23: Total number of patients on type 1 real time CGM with alarms
        """
        return kpi_23_type1_real_time_cgm_with_alarms(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_24(self) -> dict:
        """
        Calculates KPI 24: Total number of patients on hybrid closed loop system
        """
        return kpi_24_hybrid_closed_loop_system(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_25(self) -> dict:
        """
        Calculates KPI 25: Total number of patients with HbA1c
        """
        return kpi_25_hba1c(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_26(self) -> dict:
        """
        Calculates KPI 26: Total number of patients with BMI
        """
        return kpi_26_bmi(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_27(self) -> dict:
        """
        Calculates KPI 27: Total number of patients with thyroid screen
        """
        return kpi_27_thyroid_screen(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_28(self) -> dict:
        """
        Calculates KPI 28: Total number of patients with blood pressure
        """
        return kpi_28_blood_pressure(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_29(self) -> dict:
        """
        Calculates KPI 29: Total number of patients with urinary albumin
        """
        return kpi_29_urinary_albumin(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_30(self) -> dict:
        """
        Calculates KPI 30: Total number of patients with retinal screening
        """
        return kpi_30_retinal_screening(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_31(self) -> dict:
        """
        Calculates KPI 31: Total number of patients with foot examination
        """
        return kpi_31_foot_examination(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_32(self) -> dict:
        """
        Calculates KPI 32: Total number of patients with health check completion rate
        """
        return kpi_32_health_check_completion_rate(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_33(self) -> dict:
        """
        Calculates KPI 33: Total number of patients with HbA1c 4+
        """
        return kpi_33_hba1c_4plus(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_34(self) -> dict:
        """
        Calculates KPI 34: Total number of patients with psychological assessment
        """
        return kpi_34_psychological_assessment(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_35(self) -> dict:
        """
        Calculates KPI 35: Total number of patients with smoking status screened
        """
        return kpi_35_smoking_status_screened(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_36(self) -> dict:
        """
        Calculates KPI 36: Total number of patients with referral to smoking cessation service
        """
        return kpi_36_referral_to_smoking_cessation_service(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_37(self) -> dict:
        """
        Calculates KPI 37: Total number of patients with additional dietetic appointment offered
        """
        return kpi_37_additional_dietetic_appointment_offered(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_38(self) -> dict:
        """
        Calculates KPI 38: Total number of patients attending additional dietetic appointment
        """
        return kpi_38_patients_attending_additional_dietetic_appointment(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_39(self) -> dict:
        """
        Calculates KPI 39: Total number of patients with influenza immunisation recommended
        """
        return kpi_39_influenza_immunisation_recommended(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_40(self) -> dict:
        """
        Calculates KPI 40: Total number of patients with sick day rules advice
        """
        return kpi_40_sick_day_rules_advice(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_41(self) -> dict:
        """
        Calculates KPI 41: Total number of patients with coeliac disease screening
        """
        return kpi_41_coeliac_disease_screening(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_42(self) -> dict:
        """
        Calculates KPI 42: Total number of patients with thyroid disease screening
        """
        return kpi_42_thyroid_disease_screening(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_43(self) -> dict:
        """
        Calculates KPI 43: Total number of patients with carbohydrate counting education
        """
        return kpi_43_carbohydrate_counting_education(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_44(self) -> dict:
        """
        Calculates KPI 44: Total number of patients with mean HbA1c
        """
        return kpi_44_mean_hba1c(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_45(self) -> dict:
        """
        Calculates KPI 45: Total number of patients with median HbA1c
        """
        return kpi_45_median_hba1c(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_46(self) -> dict:
        """
        Calculates KPI 46: Total number of patients with number of admissions
        """
        return kpi_46_number_of_admissions(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_47(self) -> dict:
        """
        Calculates KPI 47: Total number of patients with number of DKA admissions
        """
        return kpi_47_number_of_dka_admissions(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_48(self) -> dict:
        """
        Calculates KPI 48: Total number of patients with required additional psychological support
        """
        return kpi_48_required_additional_psychological_support(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )

    def calculate_kpi_numerator_49(self) -> dict:
        """
        Calculates KPI 49: Total number of patients with albuminuria present
        """
        return kpi_49_albuminuria_present(
            patients=self.patients,
            audit_start_date=self.audit_start_date,
            audit_end_date=self.audit_end_date,
        )


# WIP simply return KPI Agg result for given PDU
class KPIAggregationForPDU(TemplateView):

    def get(self, request, *args, **kwargs):

        pz_code = kwargs.get("pz_code", None)

        aggregated_data = CalculateKPIS(pz_code=pz_code).calculate_kpis_for_patients()

        # Collate aggregated data
        return JsonResponse(aggregated_data, safe=False)
