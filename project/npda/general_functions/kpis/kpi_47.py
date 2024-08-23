from typing import List
from django.apps import apps
from django.db.models import Q


def kpi_47_number_of_dka_admissions(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 47: Number of DKA admissions

    Numerator: Total number of admissions with a reason for admission (item 50) that is 2 = DKA AND with a start date (item 48) OR discharge date (item 49) within the audit period
    Denominator: Total number of eligible patients (measure 1)
    """
    Visit = apps.get_model("npda", "Visit")
    eligible_visits = Visit.objects.filter(
        Q(patient__in=patients)
        & (
            Q(hospital_admission_date__range=(audit_start_date, audit_end_date))
            | Q(hospital_discharge_date__range=(audit_start_date, audit_end_date))
        )
        & Q(hospital_admission_reason=2)
    ).distinct()

    return eligible_visits.count()
