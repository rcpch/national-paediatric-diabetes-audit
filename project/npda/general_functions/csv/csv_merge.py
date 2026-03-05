from project.constants.csv_headings import CSV_HEADING_OBJECTS
from project.constants.sex_types import SEX_TYPE


def merge_sex_values(values_by_date):
    UNKNOWN = SEX_TYPE[-1][0] # 99

    # Moving from UNKNOWN to known is not an error (but moving back to it is)
    seen_non_unkown_value = False
    seen_unknown_value_before_non_unknown_value = False
    
    acc = {}

    for (date, value) in values_by_date:
        if value == UNKNOWN and not seen_non_unkown_value:
            seen_unknown_value_before_non_unknown_value = True
            continue
        
        seen_non_unkown_value = True

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
            return UNKNOWN, False # not inconsistent, just unknown
        
        return None, True # no information at all, flag as error
    
    sorted_values = sorted(acc.items(), key=lambda item: (item[1]["count"], item[1]["most_recent_date"]))

    most_common_value = sorted_values[-1][0]

    flag_errors = len(acc.keys()) > 1

    return most_common_value, flag_errors
    




def most_recent_modal_value_by_visit_date(identifier_heading, rows, column):
    # NPDA analysis has this notion of "Most up-to-date valid mode"
    # My understanding of it is that you should:
    #  - Work out the modal (most common) value
    #  - If there's more than one mode, return the one from the row with the most recent visit
    values_by_count_and_last_visit_date = rows.groupby(column).agg(
        Count=(identifier_heading, 'count'),
        LastVisitDate=('Visit/Appointment Date', 'max')
    ).sort_values(by=['Count', 'LastVisitDate'])

    if len(values_by_count_and_last_visit_date) > 0:
        return values_by_count_and_last_visit_date.iloc[-1].name

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
        unique_values = rows[heading].dropna().unique()

        if len(unique_values) > 1:
            unique_values_str = ", ".join(unique_values.astype(str))
            error_field = model_field if model_field else "__all__"
            errors_to_return[patient_row_index][error_field].append(
                f"Conflicting values for {heading}: {unique_values_str}"
            )

        match model_field:
            case "date_of_birth" | "sex" | "ethnicity":
                rows[heading] = most_recent_modal_value_by_visit_date(identifier_heading, rows, heading)
            case "reason_leaving_service":
                rows[heading] = smallest_code_with_attached_date(rows, "Reason for leaving service", "Date of leaving service")
            case "diabetes_type" | "postcode" | "gp_practice_ods_code":
                rows[heading] = most_recent_by_visit_date(rows, heading)
            case "diagnosis_date":
                rows[heading] = smallest(rows, heading)


def merge_rows_for_patient(identifier_heading, rows, patient_row_index, errors_to_return):
    for column in CSV_HEADING_OBJECTS:
        merge_patient_rows_for_column(identifier_heading, column, rows, patient_row_index, errors_to_return)