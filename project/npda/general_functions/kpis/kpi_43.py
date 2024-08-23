from datetime import timedelta
from typing import List
from django.apps import apps
from django.db.models import F, Q


def kpi_43_carbohydrate_counting_education(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 43: Carbohydrate counting education (%)

    Numerator: Number of eligible patients with an entry for Carbohydrate Counting Education (item 42) within 7 days before or 14 days after the Date of Diabetes Diagnosis (item 7)
    Denominator: Number of patients with Type 1 diabetes who were diagnosed at least 90 days before the end of the audit period
    """
    Visit = apps.get_model("npda", "Visit")
    eligible_visits = Visit.objects.filter(
        Q(
            patient__in=patients,
            carbohydrate_counting_level_three_education_date__range=(
                F("patient__diagnosis_date") - timedelta(days=7),
                F("patient__diagnosis_date") + timedelta(days=14),
            ),
        )
    ).distinct()

    return eligible_visits.count()
