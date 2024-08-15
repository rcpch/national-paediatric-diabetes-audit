from datetime import date


def validate_date(
    date_under_examination_field_name,
    date_under_examination_label_name,
    date_under_examination,
    date_of_birth,
    date_of_diagnosis,
    date_of_death=None,
):
    """
    Dates passed in are already validated as date objects
    This method validates the dates themselves
    """
    errors = []
    valid = True

    if date_under_examination is None:
        return valid, None

    if date_of_birth is not None:
        if date_under_examination < date_of_birth:
            error = {
                f"{date_under_examination_field_name}": [
                    f"'{date_under_examination_label_name}' cannot be before date of birth."
                ]
            }
            errors.append(error)
            valid = False

    if date_of_diagnosis is not None:
        if date_under_examination < date_of_diagnosis:
            error = {
                f"{date_under_examination_field_name}": [
                    f"'{date_under_examination_label_name}' cannot be before date of diagnosis."
                ]
            }
            errors.append(error)
            valid = False

    if date_of_death is not None:
        if date_under_examination > date_of_death:
            error = {
                f"{date_under_examination_field_name}": [
                    f"'{date_under_examination_label_name}' cannot be after date of death."
                ]
            }
            errors.append(error)
            valid = False

    return valid, errors
