from project.npda.general_functions.csv.csv_merge import merge_sex_values
from project.constants.sex_types import SEX_TYPE

def test_consistent_sex():
    data = [
        ("2026/01/01", SEX_TYPE[0][0]),
        ("2026/02/01", SEX_TYPE[0][0]),
        ("2026/03/01", SEX_TYPE[0][0]),
    ]

    output, flag_values = merge_sex_values(data)

    assert output == SEX_TYPE[0][0]
    assert flag_values == False


def test_inconsistent_sex():
    data = [
        ("2026/01/01", SEX_TYPE[0][0]),
        ("2026/02/01", SEX_TYPE[0][0]),
        ("2026/03/01", SEX_TYPE[1][0]),
        ("2026/04/01", SEX_TYPE[1][0]),
    ]

    output, flag_values = merge_sex_values(data)

    assert output == SEX_TYPE[1][0]
    assert flag_values == True


def test_moving_from_unknown_sex_to_known():
    data = [
        ("2026/01/01", SEX_TYPE[3][0]),
        ("2026/02/01", SEX_TYPE[3][0]),
        ("2026/03/01", SEX_TYPE[1][0]),
        ("2026/04/01", SEX_TYPE[1][0]),
    ]

    output, flag_values = merge_sex_values(data)

    assert output == SEX_TYPE[1][0]
    assert flag_values == False


def test_unknown_sex_most_recent_value():
    data = [
        ("2026/01/01", SEX_TYPE[1][0]),
        ("2026/02/01", SEX_TYPE[1][0]),
        ("2026/03/01", SEX_TYPE[3][0]),
        ("2026/04/01", SEX_TYPE[3][0]),
    ]

    output, flag_values = merge_sex_values(data)

    assert output == SEX_TYPE[3][0]
    assert flag_values == True


def test_consistent_sex():
    data = [
        ("2026/01/01", SEX_TYPE[0][0]),
        ("2026/02/01", SEX_TYPE[0][0]),
        ("2026/03/01", SEX_TYPE[0][0]),
    ]

    output, flag_values = merge_sex_values(data)

    assert output == SEX_TYPE[0][0]
    assert flag_values == False


def test_inconsistent_sex():
    data = [
        ("2026/01/01", SEX_TYPE[0][0]),
        ("2026/02/01", SEX_TYPE[0][0]),
        ("2026/03/01", SEX_TYPE[1][0]),
        ("2026/04/01", SEX_TYPE[1][0]),
    ]

    output, flag_values = merge_sex_values(data)

    assert output == SEX_TYPE[1][0]
    assert flag_values == True


def test_moving_from_unknown_to_known():
    data = [
        ("2026/01/01", SEX_TYPE[3][0]),
        ("2026/02/01", SEX_TYPE[3][0]),
        ("2026/03/01", SEX_TYPE[1][0]),
        ("2026/04/01", SEX_TYPE[1][0]),
    ]

    output, flag_values = merge_sex_values(data)

    assert output == SEX_TYPE[1][0]
    assert flag_values == False


def test_unknown_sex_most_recent_value():
    data = [
        ("2026/01/01", SEX_TYPE[1][0]),
        ("2026/02/01", SEX_TYPE[1][0]),
        ("2026/03/01", SEX_TYPE[3][0]),
        ("2026/04/01", SEX_TYPE[3][0]),
    ]

    output, flag_values = merge_sex_values(data)

    assert output == SEX_TYPE[3][0]
    assert flag_values == True