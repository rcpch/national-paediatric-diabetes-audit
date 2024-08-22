from typing import List
from django.apps import apps
from django.db.models import Q



def kpi_11_total_thyroids(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 11: Number of patients with thyroid  disease
    Number of eligible patients (measure 1)
    whose most recent observation for item 35 (based on visit date)
    is either 2 = Thyroxine for hypothyroidism or 3 = Antithyroid medication for hyperthyroidism
    """
    Visit = apps.get_model("npda", "Visit")
    eligible_patients = Visit.objects.filter(Q(
        Q(patient__in=patients) &
        Q(thyroid_treatment_status__in=[2, 3]) &
        Q(visit_date__range=(audit_start_date, audit_end_date)
    )).distinct()

    return eligible_patients.count()
