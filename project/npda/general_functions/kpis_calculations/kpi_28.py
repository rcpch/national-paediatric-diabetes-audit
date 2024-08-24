from typing import List
from django.apps import apps
from django.db.models import Q


def kpi_28_blood_pressure(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 28: Blood Pressure (%)

    Numerator: Number of eligible patients with a valid entry for systolic measurement (item 23) with an observation date (item 25) within the audit period
    Denominator: Number of patients with Type 1 diabetes aged 12+ with a complete year of care in audit period (measure 6)
    """
    Visit = apps.get_model("npda", "Visit")
    eligible_patients = Visit.objects.filter(
        Q(patient__in=patients)
        & Q(systolic_blood_pressure__isnull=False)
        & Q(height__isnull=False)
        & Q(blood_pressure_observation_date__range=(audit_start_date, audit_end_date))
    ).distinct()

    return eligible_patients.count()
