# Object types
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Optional

from django.db.models import QuerySet

from project.npda.models import Patient


@dataclass
class KPIResult:
    """
    Example would be:

    `return_patient_querysets` == False
    {
        'total_eligible': 100,
        'total_ineligible': 50,
        'total_passed': 75,
        'total_failed': 25,
        'patient_querysets': None
    }

    `return_patient_querysets` == True
    {
        'total_eligible': 100,
        'total_ineligible': 50,
        'total_passed': 75,
        'total_failed': 25,
        'patient_querysets': {
            'eligible': <QuerySet[Patient]>,
            'ineligible': <QuerySet[Patient]>,
            'passed': <QuerySet[Patient]>,
            'failed': <QuerySet[Patient]>,
        }
    }
    """

    total_eligible: int
    total_ineligible: int
    total_passed: int
    total_failed: int
    patient_querysets: Optional[Dict[str, QuerySet[Patient]]] = None


@dataclass
class KPICalculationsObject:
    calculation_datetime: datetime
    audit_start_date: date
    audit_end_date: date
    total_patients_count: int
    calculated_kpi_values: Dict[
        str,
        KPIResult,
    ]
