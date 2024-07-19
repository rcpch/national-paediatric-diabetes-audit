"""Views for KPIs"""

# Python imports

# Django imports
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db.models import Count, Avg
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import QuerySet

# NPDA Imports
from project.npda.models import Site, Patient, Visit, AuditCohort
from project.npda.views.mixins import CheckPDUListMixin, LoginAndOTPRequiredMixin
from project.npda.general_functions import get_audit_period_for_date


class CalculateKPIS:

    def __init__(self, audit_cohort: AuditCohort):
        """Calculates KPIs for given audit_cohort"""
        self.audit_cohort = audit_cohort
        self.patients = audit_cohort.patients.all()
        return self.calculate_kpis_for_patients()

    def calculate_kpi_1_total_eligible(self) -> dict:
        """Calculates KPI 1: Total number of eligible patients
        Total number of patients with:
            * a valid NHS number -> NOTE: must be valid to be saved in model
            *a valid date of birth -> NOTE: must be valid to be saved in model
            *a valid PDU number -> NOTE: must be valid to be saved in model
            * a visit date or admission date within the audit period
            * Below the age of 25 at the start of the audit period
        """

        # Get all patients in audit_cohort
        patients = self.patients.visits
        
        # Get current audit cohort's start and end date bounds
        # Get the month of the audit cohort
        cohort_month_for_audit_bounds = self.audit_cohort.quarter
        if cohort_month_for_audit_bounds >=2:
            audit_date= date(self.audit_cohort.audit_year, 4, 1)
        audit_start_date, audit_end_date = get_audit_period_for_date(self.audit_cohort.)
        
        # Filter for these all these patients' visits
        visits = Visit.objects.filter(
            patient__in=patients,
        )

        return result

    def calculate_kpis_for_patients(self) -> dict:
        """Calculate KPIs for given audit_cohort"""

        kpi_1_total_eligible = self.calculate_kpi_1_total_eligible()

        return {
            "kpi_1_total_eligible": kpi_1_total_eligible,
        }


# WIP simply return KPI Agg result for given PDU
class KPIAggregationForPDU(TemplateView):

    def get(self, request, *args, **kwargs):

        pz_code = kwargs.get("pz_code", None)

        # Get current audit cohort
        audit_cohort = AuditCohort.objects.get(
            pz_code=pz_code,
            audit_year=2024,
            quarter=2,
        )

        aggregated_data = CalculateKPIS(audit_cohort)

        # Collate aggregated data
        return JsonResponse(aggregated_data, safe=False)
