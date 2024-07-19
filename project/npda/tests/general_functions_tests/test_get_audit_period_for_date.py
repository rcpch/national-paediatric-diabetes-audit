import logging
import pytest
from datetime import date
from dateutil.relativedelta import relativedelta

from project.npda.general_functions import get_audit_period_for_date

# Logging
logger = logging.getLogger(__name__)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "input_date,expected_date_bounds",
    [
        (
            date(2024, 4, 1),
            (date(2024, 4, 1), date(2025, 3, 31)),
        ),  # Start of the 2024 audit year
        (
            date(2025, 3, 31),
            (date(2024, 4, 1), date(2025, 3, 31)),
        ),  # End of the 2024 audit year
        (
            date(2025, 4, 1),
            (date(2025, 4, 1), date(2026, 3, 31)),
        ),  # Start of the 2025 audit year
        (
            date(2026, 3, 31),
            (date(2025, 4, 1), date(2026, 3, 31)),
        ),  # End of the 2025 audit year
        (
            date(2026, 4, 1),
            (date(2026, 4, 1), date(2027, 3, 31)),
        ),  # Start of the 2026 audit year
        (
            date(2027, 3, 31),
            (date(2026, 4, 1), date(2027, 3, 31)),
        ),  # End of the 2026 audit year
    ],
)
def test_get_audit_period_for_date_returns_correct_start_and_end_date_bounds(
    input_date, expected_date_bounds
):
    assert get_audit_period_for_date(input_date) == expected_date_bounds
