from enum import Enum
import logging 

from django.core.exceptions import ValidationError
from django.db import IntegrityError

# Logging
logger = logging.getLogger(__name__)

class ValidationErrorsMixin:
    """
    A mixin to handle custom validation errors and update the 'errors' field
    in a model using enums for error messages.
    
    The purpose is to allow invalid data to be stored in the model, but still
    provide feedback to the user about the errors in a structured way.
    """

    def add_error(self, field_name: str, error_enum: Enum):
        """
        Adds the error enum to the errors field for the specified field using enum.
        
        field_name: The name of the field as a string.
        error_enum: The error enum
        """
        # Validate if the field_name exists in the model
        if not self._meta.get_field(field_name):
            raise ValueError(f"The field '{field_name}' does not exist in the model '{self.__class__.__name__}'.")

        # Initialize the errors field if it is None
        if self.errors is None:
            self.errors = {}

        if field_name not in self.errors:
            self.errors[field_name] = []

        # Store the name of the enum (e.g., 'DOB_IN_FUTURE')
        # to allow for JSON serialization
        self.errors[field_name].append(error_enum.name)


    def validate_fields(self):
        """
        Validate fields and populate the 'errors' field if any invalid data is found.
        Override this method in the subclass to implement custom validation logic.
        """
        raise NotImplementedError("Subclasses must implement validate_fields method.")

    def handle_invalid_choice(self, field_name, error_message):
        """
        Handle invalid choices for specific fields. Can be overridden in models.
        By default, it adds the error to the errors field.
        """
        self.add_error(field_name, error_message)
    
    def full_clean(self, *args, **kwargs):
        """
        Override full_clean method to include custom validation.
        
        We capture specified ValidationErrors and store them in the 'errors' field.
        
        ValidationErrors not specified in `get_fields_with_custom_choice_handling` will still raise a ValidationError.
        """
        try:
            # Perform the standard validation first
            super().full_clean(*args, **kwargs)
        except ValidationError as e:
            # Capture and handle validation errors
            logger.debug(f'validation error: {e.messages=} {e.message_dict=} {e.error_dict=}')
            for field, error_messages in e.message_dict.items():
                
                # Allow invalid choices in specified fields
                if field in self.get_fields_with_custom_choice_handling():
                    # Skip re-raising the exception for these fields
                    # Capture the invalid choice error
                    # NOTE: error_messages is a single-element list of strings
                    self.handle_invalid_choice(field, error_messages[0])
                else:
                    # Re-raise the error for critical fields
                    raise e

        # Call the model-specific validation logic
        self.validate_fields()

    def save(self, *args, **kwargs):
        # Reset errors field before saving
        self.errors = None

        # Run full_clean to trigger validation and populate errors
        try:
            self.full_clean()
        except ValidationError as e:
            # Django validation errors should prevent saving, so re-raise the exception
            raise e

        # Custom errors can be present, but the model will still be saved
        self.is_valid = not bool(self.errors)

        return super().save(*args, **kwargs)

    def get_fields_with_custom_choice_handling(self):
        """
        Return a list of fields that should have custom choice handling.
        Default implementation returns an empty list, meaning no custom handling.
        """
        return []