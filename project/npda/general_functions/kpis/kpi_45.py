from datetime import timedelta
from typing import List
from django.apps import apps
from django.db.models import Q, F, FloatField, ExpressionWrapper
from django.db.models.functions import PercentRank


def kpi_45_median_hba1c(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 45: Median HbA1c

    Numerator: Median of HbA1c measurements (item 17) within the audit period, excluding measurements waken within 90 days of diagnosis
    Denominator: Total number of eligible patients (measure 1)
    """
    Visit = apps.get_model("npda", "Visit")

    # Step 1: Get the eligible visits
    eligible_visits = (
        Visit.objects.filter(
            Q(patient__in=patients)
            & Q(hba1c_date__range=(audit_start_date, audit_end_date))
        )
        .exclude(
            Q(
                hba1c_date__range=(
                    F("patient__diagnosis_date"),
                    F("patient__diagnosis_date") + timedelta(days=90),
                )
            )
        )
        .distinct()
    )

    # Step 2: Annotate visits with percent rank
    eligible_visits = eligible_visits.annotate(
        percent_rank=PercentRank().over(order_by="hba1c")
    )

    # Step 3: Calculate the median by filtering percent ranks close to 0.5
    median_hba1c_entry = (
        eligible_visits.annotate(
            diff_from_median=ExpressionWrapper(
                F("percent_rank") - 0.5, output_field=FloatField()
            )
        )
        .order_by("diff_from_median")
        .first()
    )

    hba1c_median = median_hba1c_entry.hba1c if median_hba1c_entry else None
    return hba1c_median
