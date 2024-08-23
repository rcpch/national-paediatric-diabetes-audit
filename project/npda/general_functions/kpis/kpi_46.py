from typing import List
from django.apps import apps
from django.db.models import F, Q


def kpi_46_number_of_admissions(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 46: Number of admissions

    Numerator: Total number of admissions with a valid reason for admission (item 50) AND with a start date (item 48) OR discharge date (item 49)within the audit period
    Denominator: Total number of eligible patients (measure 1)
    """
    Visit = apps.get_model("npda", "Visit")
    eligible_visits = Visit.objects.filter(
        Q(hospital_admission_date__range=(audit_start_date, audit_end_date))
        | Q(hospital_discharge_date__range=(audit_start_date, audit_end_date))
        & Q(hospital_admission_reason__isnull=False)
        & Q(patient__in=patients),
    ).distinct()

    return eligible_visits.count()
