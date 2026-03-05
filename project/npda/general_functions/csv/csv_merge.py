import pandas as pd

from project.constants.csv_headings import CSV_HEADING_OBJECTS
from project.constants.sex_types import SEX_TYPE
from project.constants.ethnicities import ETHNICITIES


def most_recent_modal_value_by_visit_date(values_by_date, unknown_value):
    # Moving from UNKNOWN to known is not an error (but moving back to it is)
    seen_non_unknown_value = False
    seen_unknown_value_before_non_unknown_value = False
    
    acc = {}

    for (date, value) in values_by_date:
        if value == unknown_value and not seen_non_unknown_value:
            seen_unknown_value_before_non_unknown_value = True
            continue
        
        seen_non_unknown_value = True

        if value in acc:
            acc[value]["count"] += 1

            if date > acc[value]["most_recent_date"]:
                acc[value]["most_recent_date"] = date
        else:
            acc[value] = {
                "count": 1,
                "most_recent_date": date,
            }

    
    if len(acc) == 0:
        if seen_unknown_value_before_non_unknown_value:
            return unknown_value, False # not inconsistent, just unknown
        
        return None, True # no information at all, flag as error
    
    sorted_values = sorted(acc.items(), key=lambda item: (item[1]["count"], item[1]["most_recent_date"]))

    most_common_value = sorted_values[-1][0]

    flag_errors = len(acc.keys()) > 1

    return most_common_value, flag_errors

def smallest(rows, column):
    if len(rows) > 0:
        return rows[column].min()

def smallest_code_with_attached_date(rows, code_column, date_column):
    rows_with_leaving_service = rows.dropna(subset=[date_column]).sort_values(by=code_column)

    if len(rows_with_leaving_service) > 0:
        return rows_with_leaving_service.iloc[0][code_column]

def most_recent_by_visit_date(rows, column):
    if rows['Visit/Appointment Date'].isnull().all():
        # Unlikely case where there are no visit dates at all (to cover tests)
        return rows.iloc[0][column]

    rows_with_value = rows.dropna(subset=[column])

    if len(rows_with_value) == 0:
        return None

    most_recent_row = rows.loc[rows_with_value['Visit/Appointment Date'].idxmax()]

    return most_recent_row[column]

def merge_patient_rows_for_column(identifier_heading, column, rows, patient_row_index, errors_to_return):
    heading = column["heading"]

    model = column.get("model")
    model_field = column.get("model_field")

    if model in ["Patient", "Transfer"]:
        values_by_date = ((row["Visit/Appointment Date"], row[heading]) for _, row in rows.iterrows() if pd.notnull(row[heading]))
        unique_values = rows[heading].dropna().unique()

        flag_values = False

        match model_field:
            case "date_of_birth":
                rows[heading], flag_values = most_recent_modal_value_by_visit_date(values_by_date, unknown_value=None)
            case "sex":
                rows[heading], flag_values = most_recent_modal_value_by_visit_date(values_by_date, unknown_value=SEX_TYPE[-1][0])
            case "ethnicity":
                rows[heading], flag_values = most_recent_modal_value_by_visit_date(values_by_date, unknown_value=ETHNICITIES[-1][0])
            case "reason_leaving_service":
                rows[heading] = smallest_code_with_attached_date(rows, "Reason for leaving service", "Date of leaving service")
                flag_values = True
            case "diabetes_type" | "postcode" | "gp_practice_ods_code":
                rows[heading] = most_recent_by_visit_date(rows, heading)
                flag_values = True
            case "diagnosis_date":
                rows[heading] = smallest(rows, heading)
                flag_values = True
        
        if len(unique_values) > 1 and flag_values:
            unique_values_str = ", ".join(unique_values.astype(str))
            error_field = model_field if model_field else "__all__"
            errors_to_return[patient_row_index][error_field].append(
                f"Conflicting values for {heading}: {unique_values_str}"
            )


def merge_rows_for_patient(identifier_heading, rows, patient_row_index, errors_to_return):
    for column in CSV_HEADING_OBJECTS:
        merge_patient_rows_for_column(identifier_heading, column, rows, patient_row_index, errors_to_return)