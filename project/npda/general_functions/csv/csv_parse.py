# python imports
import collections
import logging
import re
from dataclasses import dataclass

import numpy as np

# Third-party imports
import pandas as pd

# RCPCH imports
from project.constants import (
    ALL_DATES,
    CSV_DATA_TYPES_MINUS_DATES,
    CSV_HEADING_OBJECTS,
    ENGLAND_CSV_DATA_TYPES,
    JERSEY_CSV_DATA_TYPES,
    UNIQUE_IDENTIFIER_ENGLAND,
    UNIQUE_IDENTIFIER_JERSEY,
    csv_definition_for,
)

# Django imports


# Logging setup
logger = logging.getLogger(__name__)


@dataclass
class ParsedCSVFile:
    df: pd.DataFrame
    identifier_column: str | None
    template_columns: list[str]
    missing_columns: list[str]
    additional_columns: list[str]
    duplicate_columns: list[str]
    parse_type_error_columns: list[str]
    # Gather all error messages indexed by row number and the field that caused them
    # csv_upload also has one of these and they are merged before saving
    # NB: the nested dict is keyed by model field name, not CSV heading
    # dict[number, dict[str, list[str]]]
    errors_to_return: collections.defaultdict[
        int, collections.defaultdict[str, list[str]]
    ]


def csv_parse(csv_file):
    """
    Read the csv file and return a pandas dataframe
    Assigns the correct data types to the columns
    Parses the dates in the columns to the correct format
    """
    # It is possible the csv file has no header row. In this case, we will use the predefined column names
    # The predefined column names are in the HEADINGS_LIST constant and if cast to lowercase, in lowercase_headings_list
    # We will check if the first row of the csv file matches the predefined column names
    # If it does not, we will use the predefined column names
    # If it does, we will use the column names in the csv file
    # The exception is if the first row of the csv file does not match any of the predefined column names, in which case we will reject the csv

    errors_to_return = collections.defaultdict(lambda: collections.defaultdict(list))

    HEADINGS_OBJECTS = (
        UNIQUE_IDENTIFIER_ENGLAND + UNIQUE_IDENTIFIER_JERSEY + CSV_HEADING_OBJECTS
    )
    HEADINGS_LIST = [obj["heading"] for obj in HEADINGS_OBJECTS]

    # Convert the predefined column names to lowercase
    lowercase_headings_list = [heading.lower() for heading in HEADINGS_LIST]

    # Read the first row of the csv file
    try:
        df = pd.read_csv(csv_file, encoding="utf-8")
    except UnicodeDecodeError:
        # This is the default you get from Excel when saving on a UK English machine
        # Other encodings are unlikely. Our dataset doesn't expect non-ASCII characters
        # but we have seen non-breaking spaces sneak in (https://github.com/rcpch/national-paediatric-diabetes-audit/issues/999)
        csv_file.seek(0)
        df = pd.read_csv(csv_file, encoding="ISO-8859-1")

    if any(col.lower() in lowercase_headings_list for col in df.columns):
        # The first row of the csv file matches at least some of the predefined column names
        # We will use the column names in the csv file
        pass
    else:
        # The first row of the csv file does not match the predefined column names
        # We will reject this csv (#391)
        raise ValueError(
            "The first row of the csv file does not match any of the predefined column names. Please include these and upload the file again."
        )

    # Remove leading and trailing whitespace on column names
    # The template published on the RCPCH website has trailing spaces on 'Observation Date: Thyroid Function '
    df.columns = df.columns.str.strip()

    # issue #1038 - Twinkle users inexplicably submit CSV files with headings that are in quotes.
    df.columns = df.columns.str.strip("'\"")

    # Replace headings which were different from in the old NPDA template with the new
    for column in df.columns:
        lowercase_col = column.lower()

        for heading in HEADINGS_OBJECTS:
            if "alternative_headings" in heading:
                lowercase_alternative_headings = [
                    h.lower() for h in heading["alternative_headings"]
                ]

                if lowercase_col in lowercase_alternative_headings:
                    df = df.rename(columns={column: heading["heading"]})

    # Pandas has strange behaviour for the first line in a CSV - additional cells become row labels
    # https://github.com/pandas-dev/pandas/issues/47490
    #
    # As a heuristic for this, check the row label for the first row is the number 0
    # If it isn't - you've got too many values in the first row
    if not df.iloc[0].name == 0:
        raise ValueError(
            "Suspected too many values in the first row, please check there are no extra values"
        )

    # Accept columns case insensitively but replace them with their official version to make life easier later
    for column in df.columns:
        if column not in HEADINGS_LIST and column.lower() in lowercase_headings_list:
            normalised_column = next(
                c for c in HEADINGS_LIST if c.lower() == column.lower()
            )
            df = df.rename(columns={column: normalised_column})

    identifier_england = UNIQUE_IDENTIFIER_ENGLAND[0]["heading"]
    identifier_jersey = UNIQUE_IDENTIFIER_JERSEY[0]["heading"]

    # Ensure exactly one identifier column is present
    if not ((identifier_england in df.columns) ^ (identifier_jersey in df.columns)):
        # If both are present
        if identifier_england in df.columns and identifier_jersey in df.columns:
            user_error_message = "Both Unique Reference Number and NHS Number columns are present. Please ensure only one of these is present in the file."
        # Neither present
        else:
            user_error_message = "No unique identifier column is present. Please ensure one of Unique Reference Number or NHS Number is present in the file."
        raise ValueError(user_error_message)

    # Set the identifier column
    if identifier_jersey in df.columns:
        identifier_column = identifier_jersey
        _headings_list = [
            heading for heading in HEADINGS_LIST if heading != identifier_england
        ]

        # Gather missing / additional columns
        missing_columns = list(set(_headings_list) - set(df.columns))
        additional_columns = list(set(df.columns) - set(_headings_list))
    else:
        identifier_column = identifier_england
        _headings_list = [
            heading for heading in HEADINGS_LIST if heading != identifier_jersey
        ]

        # Gather missing / additional columns
        missing_columns = list(set(_headings_list) - set(df.columns))
        additional_columns = list(set(df.columns) - set(_headings_list))

    # Check every row has a unique identifier
    # If not, do not progress and raise error to the user with the row number(s)
    if df[identifier_column].isna().any():
        # Get the row numbers of the rows with no identifier
        na_row_numbers = df[df[identifier_column].isna()].index.tolist()
        if len(na_row_numbers) == 1:
            user_error_message = f"Row {na_row_numbers[0]} has no {identifier_column}. Please ensure all rows have a unique identifier and upload the file again."
        else:
            user_error_message = f"{len(na_row_numbers)} rows have no {identifier_column}. Please ensure all rows have a unique identifier and upload the file again. The rows with no {identifier_column} are: {','.join(map(str, na_row_numbers))}"

        raise ValueError(user_error_message)

    # Duplicate columns appear in the dataframe as XYZ.1, XYZ.2 etc
    duplicate_columns = []

    parse_type_error_columns = []

    for column in df.columns:
        result = re.match(r"([\w ]+)\.\d+$", column)

        if result and result.group(1) not in duplicate_columns:
            duplicate_columns.append(result.group(1))

    for column in ALL_DATES:
        if column in df.columns:
            column_before = df[column].copy()
            # Support DD/MM/YYYY and DD/MM/YY
            column_after = pd.to_datetime(
                df[column], format="mixed", dayfirst=True, errors="coerce"
            )

            for row_index, (value_before, value_after) in enumerate(
                zip(column_before, column_after, strict=False)
            ):
                # Handle empty strings (including spaces) for optional date columns
                if (
                    not pd.isna(value_before)
                    and pd.isna(value_after)
                    and not (type(value_before) is str and value_before.strip() == "")
                ):
                    model_field = csv_definition_for(column)["model_field"]
                    errors_to_return[row_index][model_field].append(
                        "Date format is incorrect (expected DD/MM/YYYY)"
                    )

            df[column] = column_after

    if identifier_column == identifier_jersey:
        datatypes = JERSEY_CSV_DATA_TYPES | CSV_DATA_TYPES_MINUS_DATES
    else:
        datatypes = ENGLAND_CSV_DATA_TYPES | CSV_DATA_TYPES_MINUS_DATES

    nullable_int_types = {
        "Int8",
        "Int16",
        "Int32",
        "Int64",
        "UInt8",
        "UInt16",
        "UInt32",
        "UInt64",
    }

    # Apply the dtype to non-date columns
    for column, dtype in datatypes.items():
        try:
            if column in df.columns:
                if dtype in nullable_int_types and pd.api.types.is_float_dtype(
                    df[column]
                ):
                    # pandas 2 refuses to cast float64 → nullable int when NaN is present
                    # because numpy's safe-cast rules see NaN as non-representable.
                    # Pre-process the column via a list comprehension:
                    #   - NaN          → None  (becomes pd.NA in the Int64 series)
                    #   - integer-valued float (1.0, 2.0)  → int(v)  (valid; stored as float because of NaN elsewhere in column)
                    #   - non-integer float (99.5)          → kept as-is (bad data)
                    # When bad data is present the subsequent astype() will still raise,
                    # routing the column through parse_type_error_columns as before so
                    # that downstream validation can flag it properly.
                    # Use pd.NA (not None) so pd.Series doesn't infer float64.
                    # pd.Series([1, None]) → float64 in pandas 2.x;
                    # pd.Series([1, pd.NA]) stays object, astype('Int64') works.
                    df[column] = pd.Series(
                        [
                            pd.NA
                            if pd.isna(v)
                            else (int(v) if float(v).is_integer() else v)
                            for v in df[column]
                        ],
                        index=df.index,
                        dtype=object,
                    )
                df[column] = df[column].astype(dtype)
        except (ValueError, TypeError):
            parse_type_error_columns.append(column)
            continue

        # Convert NaN to None-y for nullable fields
        if column in df.columns:
            if dtype == "string":
                df[column] = df[column].fillna(pd.NA)
            elif dtype not in nullable_int_types:
                # nullable int columns already have pd.NA set correctly above;
                # applying where(..., None) on an Int64 series upcasts to object dtype
                df[column] = df[column].where(pd.notnull(df[column]), None)
        # round height and weight if provided to 1 decimal place
        if (
            column
            in [
                "Patient Height (cm)",
                "Patient Weight (kg)",
                "Total Cholesterol Level (mmol/l)",
                "Urinary Albumin Level (ACR)",
            ]
            and column in df.columns
        ):
            if df[column].dtype == np.float64:
                df[column] = df[column].round(1)
            else:
                parse_type_error_columns.append(column)

    template_columns = [identifier_column] + [
        obj["heading"] for obj in CSV_HEADING_OBJECTS
    ]

    return ParsedCSVFile(
        df,
        identifier_column,
        template_columns,
        missing_columns,
        additional_columns,
        duplicate_columns,
        parse_type_error_columns,
        errors_to_return,
    )
