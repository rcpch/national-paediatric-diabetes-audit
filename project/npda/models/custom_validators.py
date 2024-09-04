from datetime import date
from django.core.exceptions import ValidationError
import nhs_number

def validate_nhs_number(value):
    """Validate the NHS number using the nhs_number package."""
    if not nhs_number.is_valid(value):
        raise ValidationError(
            f"{value} is not a valid NHS number.",
            params={"value": value},
        )

def not_in_the_future_validator(value):
    """
    model level validator to prevent persisting a date in the future
    """
    if value <= date.today():
        return value
    else:
        raise ValidationError("Dates cannot be in the future.")
