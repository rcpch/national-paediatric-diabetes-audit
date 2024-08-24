from datetime import timedelta
from typing import List
from django.apps import apps
from django.db.models import F, Q


def kpi_42_thyroid_disease_screening(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 42: Thyroid disaese screening (%)

    Numerator: Number of eligible patients with an entry for Thyroid Function Observation Date (item 34) within 90 days of Date of Diabetes Diagnosis (item 7)
    Denominator: Number of patients with Type 1 diabetes who were diagnosed at least 90 days before the end of the audit period
    """
    Visit = apps.get_model("npda", "Visit")
    eligible_visits = Visit.objects.filter(
        Q(patient__in=patients),
        Q(
            thyroid_function_date__range=(
                F("patient__diagnosis_date"),
                F("patient__diagnosis_date") + timedelta(days=90),
            )
        ),
    ).distinct()

    return eligible_visits.count()
