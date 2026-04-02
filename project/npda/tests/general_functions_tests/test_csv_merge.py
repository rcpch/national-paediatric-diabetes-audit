from project.constants.sex_types import SEX_TYPE
from project.npda.general_functions.csv.csv_merge import (
    most_recent_modal_value_by_visit_date,
)


def test_consistent_sex():
    data = [
        ("2026/01/01", SEX_TYPE[0][0]),
        ("2026/02/01", SEX_TYPE[0][0]),
        ("2026/03/01", SEX_TYPE[0][0]),
    ]

    output, flag_values = most_recent_modal_value_by_visit_date(data, SEX_TYPE[-1][0])

    assert output == SEX_TYPE[0][0]
    assert not flag_values


def test_inconsistent_sex():
    data = [
        ("2026/01/01", SEX_TYPE[0][0]),
        ("2026/02/01", SEX_TYPE[0][0]),
        ("2026/03/01", SEX_TYPE[1][0]),
        ("2026/04/01", SEX_TYPE[1][0]),
    ]

    output, flag_values = most_recent_modal_value_by_visit_date(data, SEX_TYPE[-1][0])

    assert output == SEX_TYPE[1][0]
    assert flag_values


def test_moving_from_unknown_sex_to_known():
    data = [
        ("2026/01/01", SEX_TYPE[3][0]),
        ("2026/02/01", SEX_TYPE[3][0]),
        ("2026/03/01", SEX_TYPE[1][0]),
        ("2026/04/01", SEX_TYPE[1][0]),
    ]

    output, flag_values = most_recent_modal_value_by_visit_date(data, SEX_TYPE[-1][0])

    assert output == SEX_TYPE[1][0]
    assert not flag_values


def test_unknown_sex_most_recent_value():
    data = [
        ("2026/01/01", SEX_TYPE[1][0]),
        ("2026/02/01", SEX_TYPE[1][0]),
        ("2026/03/01", SEX_TYPE[3][0]),
        ("2026/04/01", SEX_TYPE[3][0]),
    ]

    output, flag_values = most_recent_modal_value_by_visit_date(data, SEX_TYPE[-1][0])

    assert output == SEX_TYPE[3][0]
    assert flag_values
