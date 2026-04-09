import datetime
import re
import unicodedata

import pandas as pd
from pandas.api.types import is_numeric_dtype

from project.constants import ETHNICITIES, get_all_dates
from project.npda.general_functions.headings import get_field_heading

"""
CSV specific cleaning and value conversion.
Validation errors should be added in the patient and visit form, not here.
"""


def clean_csv_sex(value):
    match value.lower():
        case "m" | "1":
            return 1

        case "f" | "2":
            return 2

        case "not specified" | "3":
            return 3

        case "unknown" | "99":
            return 99

        case _:
            # Return Not Known. The patient won't save in the database without a numeric value.
            return 0


def clean_csv_ethnicity(value):
    if isinstance(value, str):
        value = value.strip().upper()

        if value in ETHNICITIES:
            return value

    return value


def clean_csv_measurement(value):
    """
    Convert measurement values to float, handling empty strings and non-numeric values.
    Remove extraneous non-numeric characters if necessary.
    Returns None for empty strings or non-numeric values.
    If the value is a valid number, it will be converted to float.
    If the value is an empty string, it will return None.
    If the value cannot be converted to float, it will return None.
    """
    if value == "":
        return None
    if isinstance(value, str):
        # Return the string if it contains no digits as this will be handled by the form validation
        if not any(char.isdigit() for char in value):
            return value
        # This string now contains numbers and possibly some characters
        # Remove any non-numeric characters except for decimal points
        # This will handle cases like "5.9cm", "70kg", etc.
        # It will also remove any leading or trailing whitespace
        value = "".join(char for char in value if char.isdigit() or char == ".")
    try:
        return float(value)
    except ValueError:
        return None


def clean_whitespace(x):
    if isinstance(x, str):
        stripped = x.strip()
        return None if stripped == "" else stripped
    return x


# Clean and parse date-like columns early so Django forms receive proper dates
def clean_date_value(v):
    if pd.isna(v):
        return v
    # Already a datetime-like
    if isinstance(v, (pd.Timestamp, datetime.date)):
        return v
    s = str(v)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.replace("\u00a0", " ")
    s = s.strip()
    s = s.strip("'\"“”‘’`·†")
    s = re.sub(r"\s+", " ", s)
    return s


# Helper normalisation to robustly match noisy incoming headings
def normalise_heading(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"[^0-9a-zA-Z]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def csv_clean(df, dataset_year=2021):
    for date_col in get_all_dates(dataset_year):
        if date_col in df.columns:
            cleaned = df[date_col].apply(clean_date_value)
            df[date_col] = pd.to_datetime(
                cleaned, format="mixed", dayfirst=True, errors="coerce"
            )

    fields_to_clean = {
        "sex": clean_csv_sex,
        "ethnicity": clean_csv_ethnicity,
        "height": clean_csv_measurement,
        "weight": clean_csv_measurement,
    }

    for field, cleaner in fields_to_clean.items():
        heading = get_field_heading(field, dataset_year)

        # If the canonical heading isn't present, try to find a noisy match and rename it
        if heading not in df.columns:
            for column in df.columns:
                if normalise_heading(column) == normalise_heading(heading):
                    df = df.rename(columns={column: heading})
                    break

        if heading in df.columns and not is_numeric_dtype(df[heading]):
            df[heading] = df[heading].apply(cleaner)

    # Strip whitespace only fields of whitespaces
    for col in df.select_dtypes(include=["string", "object"]).columns:
        df[col] = df[col].apply(clean_whitespace)

    return df
