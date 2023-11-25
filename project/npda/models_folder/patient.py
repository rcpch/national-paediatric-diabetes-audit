# python imports
from datetime import date

# django imports
from django.db import models
from django.db.models import CharField, DateField, IntegerChoices

# npda imports
from ...constants import (
    ETHNICITIES,
    DIABETES_TYPES,
    SEX_TYPE,
    UNKNOWN_POSTCODES_NO_SPACES,
)
from ..general_functions import stringify_time_elapsed, imd_for_postcode


class Patient(models.Model):
    nhs_number = CharField(  # the NHS number for England and Wales
        "NHS Number", unique=True, blank=True, null=True, max_length=10
    )

    sex = models.IntegerField("Stated gender", choices=SEX_TYPE, blank=True, null=True)

    date_of_birth = DateField(
        "date of birth (YYYY-MM-DD)",
        blank=True,
        null=True,
    )
    postcode = CharField(
        "Postcode of usual address",
        max_length=8,
        blank=True,
        null=True,
    )

    ethnicity = CharField(
        "Ethnic Category", max_length=4, choices=ETHNICITIES, blank=True, null=True
    )

    index_of_multiple_deprivation_quintile = models.PositiveSmallIntegerField(
        # this is a calculated field - it relies on the availability of the RCPCH Census Platform
        # A quintile is calculated on save and persisted in the database
        "index of multiple deprivation calculated from MySociety data.",
        blank=True,
        editable=False,
        null=True,
    )

    diabetes_type = IntegerChoices(verbose_name="Diabetes Type", choices=DIABETES_TYPES)

    diagnosis_date = DateField(verbose_name="Date of Diabetes Diagnosis")

    death_date = models.DateField(
        verbose_name="Date of death",
        blank=True,
        null=True,
    )

    gp_practice_ods_code = models.CharField(verbose_name="GP Practice Code")

    def age_days(self, today_date=date.today()):
        """
        Returns the age of the patient in years, months and days
        This is a calculated field
        Date of birth is required
        Today's date is optional and defaults to date.today()
        """
        # return stringify_time_elapsed(self.date_of_birth, today_date)
        return (today_date - self.date_of_birth).days

    def age(self, today_date=date.today()):
        """
        Returns the age of the patient in years, months and days
        This is a calculated field
        Date of birth is required
        Today's date is optional and defaults to date.today()
        """
        return stringify_time_elapsed(self.date_of_birth, today_date)

    def save(self, *args, **kwargs) -> None:
        # calculate the index of multiple deprivation quintile if the postcode is present
        # Skips the calculation if the postcode is on the 'unknown' list
        if self.postcode:
            if str(self.postcode).replace(" ", "") not in UNKNOWN_POSTCODES_NO_SPACES:
                try:
                    self.index_of_multiple_deprivation_quintile = imd_for_postcode(
                        self.postcode
                    )
                except Exception as error:
                    # Deprivation score not persisted if deprivation score server down
                    self.index_of_multiple_deprivation_quintile = None
                    print(
                        f"Cannot calculate deprivation score for {self.postcode}: {error}"
                    )
                    pass
        return super().save(*args, **kwargs)
