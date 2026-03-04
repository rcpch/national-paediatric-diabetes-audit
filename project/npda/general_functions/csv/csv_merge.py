from project.constants.csv_headings import CSV_HEADING_OBJECTS

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