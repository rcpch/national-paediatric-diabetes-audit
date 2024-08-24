from typing import List
from django.apps import apps
from django.db.models import Q


def kpi_30_retinal_screening(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 30: Retinal Screening (%)

    Numerator: Number of eligible patients with at least one entry for Retinal Screening Result (item 28) is either 1 = Normal or 2 = Abnormal AND the observation date (item 27) is within the audit period
    Denominator: Number of patients with Type 1 diabetes aged 12+ with a complete year of care in audit period (measure 6)
    """
    Visit = apps.get_model("npda", "Visit")
    eligible_patients = Visit.objects.filter(
        Q(patient__in=patients)
        & (Q(retinal_screening_result=1) | Q(retinal_screening_result=2))
        & Q(
            retinal_screening_observation_date__range=(audit_start_date, audit_end_date)
        )
    ).distinct()

    return eligible_patients.count()
