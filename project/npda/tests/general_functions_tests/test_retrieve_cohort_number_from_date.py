import pytest
from project.npda.general_functions import retrieve_quarter_for_date
from datetime import date


# Test cases for retrieve_quarter_for_date function
@pytest.mark.parametrize(
    "test_input,expected",
    [
        (date(2023, 4, 1), 1),  # Start of the audit year
        (date(2023, 6, 30), 1),  # End of Q1
        (date(2023, 7, 1), 2),  # Start of Q2
        (date(2023, 9, 30), 2),  # End of Q2
        (date(2023, 10, 1), 3),  # Start of Q3
        (date(2023, 12, 31), 3),  # End of Q3
        (date(2024, 1, 1), 4),  # Start of Q4
        (date(2024, 3, 31), 4),  # End of the audit year
        (
            date(2023, 3, 31),
            4,
        ),  # Day before the audit year starts, should be in the last quarter of the previous cycle
        (date(2023, 4, 2), 1),  # Just after the audit year starts
    ],
)
def test_retrieve_quarter_for_date(test_input, expected):
    assert retrieve_quarter_for_date(test_input) == expected
