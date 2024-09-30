# Object types
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Union


@dataclass
class KPIResult:
    total_eligible: int
    total_ineligible: int
    total_passed: int
    total_failed: int


@dataclass
class KPICalculationsObject:
    pz_code: str
    calculation_datetime: datetime
    audit_start_date: date
    audit_end_date: date
    total_patients_count: int
    calculated_kpi_values: Dict[
        str,
        Union[KPIResult, str],
    ] # looks like { 'kpi_name' : KPIResult OR "Not implemented"}
