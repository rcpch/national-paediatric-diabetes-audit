# python imports
from datetime import date
import logging

# django imports
from django.apps import apps
from django.contrib.gis.db import models
from django.contrib.gis.db.models import CharField, DateField, PositiveSmallIntegerField
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from project.npda.models.custom_validators import validate_nhs_number
from project.npda.models.validation_errors_mixin import ValidationErrorsMixin

# npda imports
from ...constants import (
    ETHNICITIES,
    DIABETES_TYPES,
    SEX_TYPE,
    UNKNOWN_POSTCODES_NO_SPACES,
    CAN_LOCK_CHILD_PATIENT_DATA_FROM_EDITING,
    CAN_UNLOCK_CHILD_PATIENT_DATA_FROM_EDITING,
    CAN_OPT_OUT_CHILD_FROM_INCLUSION_IN_AUDIT,
)
from ..general_functions import (
    stringify_time_elapsed,
    imd_for_postcode,
)

# Logging
logger = logging.getLogger(__name__)

from enum import Enum

class PatientError(Enum):
    """NOT including nhs number as that error should prevent saving"""
    DOB_IN_FUTURE = "Date of birth cannot be in the future."
    PT_OLDER_THAN_19yo = "Patient is too old for the NPDA."
    INVALID_POSTCODE = "Postcode is invalid."
    DEPRIVATION_CALCULATION_FAILED = "Cannot calculate deprivation score."
    INVALID_DIABETES_TYPE = "Diabetes type is invalid."
    DIAGNOSIS_DATE_BEFORE_DOB = "Diagnosis date is before date of birth."


class Patient(ValidationErrorsMixin, models.Model):
    """
    The Patient class.

    The index of multiple deprivation is calculated in the save() method using the postcode supplied and the
    RCPCH Census Platform

    Custom methods age and age_days, returns the age.
    
    Uses the ValidationErrorsMixin to handle custom validation errors and update the 'errors' field.
    """
    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"
        ordering = (
            "pk",
            "nhs_number",
        )
        permissions = [
            CAN_LOCK_CHILD_PATIENT_DATA_FROM_EDITING,
            CAN_UNLOCK_CHILD_PATIENT_DATA_FROM_EDITING,
            CAN_OPT_OUT_CHILD_FROM_INCLUSION_IN_AUDIT,
        ]
        
    # the NHS number for England and Wales
    nhs_number = CharField(  
        "NHS Number", 
        unique=True, 
        validators=[validate_nhs_number], # Raise ValidationError & prevent saving
    )

    sex = models.IntegerField("Stated gender", choices=SEX_TYPE, blank=True, null=True)

    date_of_birth = DateField("date of birth (YYYY-MM-DD)")
    postcode = CharField(
        "Postcode of usual address",
        blank=True,
        null=True,
    )

    ethnicity = CharField(
        "Ethnic Category", max_length=4, choices=ETHNICITIES, blank=True, null=True
    )

    index_of_multiple_deprivation_quintile = models.PositiveSmallIntegerField(
        # this is a calculated field - it relies on the availability of the RCPCH Census Platform
        # A quintile is calculated on save and persisted in the database
        "index of multiple deprivation calculated from RCPCH Census Platform.",
        blank=True,
        editable=False,
        null=True,
    )

    # Separately define the diabetes type choices to allow for custom
    # handling of invalid choices
    DIABETES_TYPES = DIABETES_TYPES
    diabetes_type = PositiveSmallIntegerField(
        verbose_name="Diabetes Type", 
        blank=True,
        null=True,
    )

    diagnosis_date = DateField(verbose_name="Date of Diabetes Diagnosis")

    death_date = models.DateField(
        verbose_name="Date of death",
        blank=True,
        null=True,
    )

    gp_practice_ods_code = models.CharField(
        verbose_name="GP Practice Code", blank=True, null=True
    )

    gp_practice_postcode = models.CharField(
        verbose_name="GP Practice postcode", blank=True, null=True
    )

    is_valid = models.BooleanField(
        verbose_name="Record is valid", blank=False, null=False, default=False
    )

    # Custom field to store validation errors
    # This field is populated by the ValidationErrorsMixin
    # JSON field of structure {field_name: [PatientError1 name, PatientError2 name, ...], ...}
    errors = models.JSONField(
        verbose_name="Validation errors", blank=True, null=True, default=None
    )


    def __str__(self) -> str:
        return f"ID: {self.pk}, {self.nhs_number}"

    def get_absolute_url(self):
        return reverse("patient-detail", kwargs={"pk": self.pk})

    def get_todays_date(self) -> date:
        """Simply returns today's date. Used to enable testing of the age methods"""
        return date.today()

    # class methods
    def age_days(self, today_date=None):
        """
        Returns the age of the patient in years, months and days
        This is a calculated field
        Date of birth is required
        Today's date is optional and defaults to self.get_todays_date()):
        """
        if today_date is None:
            today_date = self.get_todays_date()
        return (today_date - self.date_of_birth).days

    def age(self, today_date=None):
        """
        Returns the age of the patient in years, months and days
        This is a calculated field
        Date of birth is required
        Today's date is optional and defaults to self.get_todays_date()):
        """
        if today_date is None:
            today_date = self.get_todays_date()
        return stringify_time_elapsed(self.date_of_birth, today_date)
        
    # Custom validation methods using ValidationErrorsMixin
    def validate_fields(self):
        """
        Can add custom validation logic here using PatientError.
        
        """
        
        TODAY = self.get_todays_date()
        
        # == `date_of_birth` ==
        if self.date_of_birth:
            # dob can't be in the future
            if self.date_of_birth > date.today():
                self.add_error('date_of_birth', PatientError.DOB_IN_FUTURE)
            
            # patient is > than 19 years old
            if self.age_days(TODAY) > 19 * 365:
                self.add_error('date_of_birth', PatientError.PT_OLDER_THAN_19yo)
                
        

        # == `postcode` ==
        if self.postcode:
            if self.postcode in UNKNOWN_POSTCODES_NO_SPACES:
                self.add_error('postcode', PatientError.INVALID_POSTCODE)
        
        # == `date_of_diagnosis` ==
        if self.diagnosis_date:
            # diagnosis date can't be before dob
            if self.diagnosis_date < self.date_of_birth:
                self.add_error('diagnosis_date', PatientError.DIAGNOSIS_DATE_BEFORE_DOB)
        
        # == `diabetes_type` ==
        if self.diabetes_type not in self.DIABETES_TYPES:
            self.add_error('diabetes_type', PatientError.INVALID_DIABETES_TYPE)
            
    
    def save(self, *args, **kwargs):
        # Custom logic to calculate deprivation score
        if self.postcode:
            try:
                self.index_of_multiple_deprivation_quintile = imd_for_postcode(self.postcode)
            except Exception as error:
                self.index_of_multiple_deprivation_quintile = None
                self.add_error('postcode', PatientError.DEPRIVATION_CALCULATION_FAILED)

        # Call the save method in the mixin
        return super().save(*args, **kwargs)

    # Custom handling for methods from ValidationErrorsMixin
    def get_fields_with_custom_choice_handling(self):
        return ['diabetes_type']
    
    # def handle_invalid_choice(self, field_name, error_message):
    #     """
    #     Custom handling for the choice fields.
    #     """
    #     if field_name == 'diabetes_type':
    #         # Add the INVALID_DIABETES_TYPE error
    #         self.add_error(field_name, PatientError.INVALID_DIABETES_TYPE)
    #     else:
    #         # For other fields, use the default behavior
    #         super().handle_invalid_choice(field_name, error_message)