from enum import Enum
from django.core.exceptions import ValidationError

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

    def full_clean(self, *args, **kwargs):
        """
        Override full_clean method to include custom validation.
        """
        # First, let Django handle the built-in validation 
        # (e.g., field constraints, unique constraints)
        super().full_clean(*args, **kwargs)

        # Then perform custom validation to add errors to the 'errors' field
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
