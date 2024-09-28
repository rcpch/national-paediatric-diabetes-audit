# Object types
from dataclasses import dataclass


@dataclass
class KPIResult:
    total_eligible: int
    total_ineligible: int
    total_passed: int
    total_failed: int