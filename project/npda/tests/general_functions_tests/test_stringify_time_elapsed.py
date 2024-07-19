from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytest
from project.npda.general_functions import stringify_time_elapsed


@pytest.mark.django_db
def test_one_year_three_months_difference():
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2023, 4, 1)
    assert stringify_time_elapsed(start_date, end_date) == "1 year, 3 months"


@pytest.mark.django_db
def test_six_months_difference():
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2022, 7, 1)
    assert stringify_time_elapsed(start_date, end_date) == "6 months"


@pytest.mark.django_db
def test_one_month_difference():
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2022, 2, 1)
    assert stringify_time_elapsed(start_date, end_date) == "1 month"


@pytest.mark.django_db
def test_one_week_difference():
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2022, 1, 8)
    assert stringify_time_elapsed(start_date, end_date) == "1 week"


@pytest.mark.django_db
def test_one_day_difference():
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2022, 1, 2)
    assert stringify_time_elapsed(start_date, end_date) == "1 day"


@pytest.mark.django_db
def test_same_day():
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2022, 1, 1)
    assert stringify_time_elapsed(start_date, end_date) == "Same day"


@pytest.mark.django_db
def test_invalid_input_end_date_none():
    start_date = datetime(2022, 1, 1)
    end_date = None
    with pytest.raises(ValueError) as e:
        stringify_time_elapsed(start_date, end_date)
    assert str(e.value) == "Both start and end dates must be provided"


@pytest.mark.django_db
def test_invalid_input_start_date_none():
    start_date = None
    end_date = datetime(2022, 1, 1)
    with pytest.raises(ValueError) as e:
        stringify_time_elapsed(start_date, end_date)
    assert str(e.value) == "Both start and end dates must be provided"


@pytest.mark.django_db
def test_end_date_before_start_date():
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2021, 1, 1)
    with pytest.raises(ValueError) as e:
        stringify_time_elapsed(start_date, end_date)
    assert str(e.value) == "End date cannot be before start date"


@pytest.mark.django_db
def test_very_large_time_difference():
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2025, 8, 24)
    assert stringify_time_elapsed(start_date, end_date) == "5 years, 7 months"
