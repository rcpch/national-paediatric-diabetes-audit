from typing import List

from django.db.models import Q


def kpi_7_total_new_diagnoses_t1dm(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 7: Total number of new diagnoses of T1DM
    Total number of patients with:
    * a valid NHS number
    * an observation within the audit period
    * Age 0-24 years at the start of the audit period
    * Diagnosis of Type 1 diabetes
    * Date of diagnosis within the audit period
    """
    eligible_patients = patients.filter(
        Q(diabetes_type=1) & Q(diagnosis_date__range=[audit_start_date, audit_end_date])
    ).distinct()

    return eligible_patients.count()
