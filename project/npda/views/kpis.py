"""Views for KPIs"""

# Python imports
from datetime import date

# Django imports
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db.models import Count, Q, Subquery
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import QuerySet

# NPDA Imports
from project.npda.models import Site, Patient, Visit, AuditCohort
from project.npda.views.mixins import CheckPDUListMixin, LoginAndOTPRequiredMixin
from project.npda.general_functions import get_audit_period_for_date


class CalculateKPIS:

    def __init__(self, pz_code: str, calculation_date: date = date.today()):
        """Calculates KPIs for given pz_code

        Params:
            * pz_code (str) - PZ code for KPIS
            * calculation_date (date) - used to define start and end date of audit period
        """
        # Set various attributes used in calculations
        self.pz_code = pz_code
        self.calculation_date = calculation_date
        # Set the start and end audit dates
        self.audit_start_date, self.audit_end_date = (
            self._get_audit_start_and_end_dates()
        )

        # Sets the KPI attribute names map
        self.kpis_names_map = self._get_kpi_attribute_names()

        # Sets relevant patients for this PZ code
        self.patients = Patient.objects.filter(
            site__paediatric_diabetes_unit_pz_code=pz_code
        )

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
        for i in range(1, 2):
            kpi_method_name = self.kpis_names_map[i]
            kpi_method = getattr(self, f"calculate_{kpi_method_name}")
            calculated_kpis[kpi_method_name] = kpi_method()

        # Calculate remaining KPIs (13-49)
        # for i in range(13, 50):
        #     kpi_method_name = self.kpis[i]
        #     kpi_method = getattr(self, f"calculate_{kpi_method_name}")
        #     calculated_kpis[kpi_method_name] = kpi_method(calculated_kpis)

        return calculated_kpis

    def calculate_kpi_1_total_eligible(self) -> dict:
        """Calculates KPI 1: Total number of eligible patients
        Total number of patients with:
            * a valid NHS number
            *a valid date of birth
            *a valid PDU number
            * a visit date or admission date within the audit period
            * Below the age of 25 at the start of the audit period
        """

        eligible_patients = self.patients.filter(
            # Valid attributes
            Q(nhs_number__isnull=False)
            & Q(date_of_birth__isnull=False)
            # NOTE: should be already filtered out when setting
            # self.patients in init method, but adding for clarity
            & Q(site__paediatric_diabetes_unit_pz_code__isnull=False)
            # Visit / admisison date within audit period
            & Q(visit__visit_date__range=(self.audit_start_date, self.audit_end_date))
            # Below the age of 25 at the start of the audit period
            & Q(
                date_of_birth__gt=self.audit_start_date.replace(
                    year=self.audit_start_date.year - 25
                )
            )
        ).distinct()

        return eligible_patients.count()


# WIP simply return KPI Agg result for given PDU
class KPIAggregationForPDU(TemplateView):

    def get(self, request, *args, **kwargs):

        pz_code = kwargs.get("pz_code", None)

        aggregated_data = CalculateKPIS(pz_code=pz_code).calculate_kpis_for_patients()

        # Collate aggregated data
        return JsonResponse(aggregated_data, safe=False)
