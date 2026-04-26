# python imports
import logging
from datetime import date

# project imports
import nhs_number
from channels.db import database_sync_to_async

# third-party imports
from dateutil.relativedelta import relativedelta
from django import forms

# django imports
from django.apps import apps
from django.core.exceptions import ValidationError

from project.constants.patient_categories import (
    PATIENT_CATEGORIES_2021,
    PATIENT_CATEGORIES_2026,
)
from project.npda.general_functions.headings import (
    PATIENT_FIELD_HEADINGS_2021,
    PATIENT_FIELD_HEADINGS_2026,
    get_field_heading,
)
from project.npda.general_functions.justification_or_standard import (
    get_field_justification_standard,
    get_field_notes,
)

from ...constants import ADHD_ASD, LEAVE_PDU_REASONS, YES_NO_UNKNOWN
from ...constants.styles.form_styles import *
from ..models import Patient, Transfer
from ..validators import not_in_the_future_validator
from .external_patient_validators import validate_patient_sync

logger = logging.getLogger(__name__)


class DateInput(forms.DateInput):
    input_type = "date"


class NHSNumberField(forms.CharField):
    def to_python(self, value):
        if not value:
            return value
        number = super().to_python(value)
        normalised = nhs_number.standardise_format(number)

        # For some combinations we get back an empty string (eg '719-573 0220')
        return normalised or value

    def validate(self, value):
        if value and not nhs_number.is_valid(value):
            raise ValidationError("Invalid NHS number")


class UniqueReferenceNumberField(forms.CharField):
    def to_python(self, value):
        if not value:
            return value
        number = super().to_python(value)
        return number

    def validate(self, value):
        if value and not value.isdigit():
            raise ValidationError("Invalid Unique Reference Number")


class PostcodeField(forms.CharField):
    def to_python(self, value):
        postcode = super().to_python(value)

        if postcode:
            return postcode.upper().replace(" ", "").replace("-", "")


class PatientForm(forms.ModelForm):
    date_leaving_service = forms.DateField(required=False, widget=DateInput())
    reason_leaving_service = forms.ChoiceField(
        required=False, choices=LEAVE_PDU_REASONS
    )
    dataset_year = 2021

    class Meta:
        model = Patient
        fields = "__all__"
        exclude = [
            "index_of_multiple_deprivation_quintile",
            "location_bng",
            "location_wgs84",
            "location_wgs",
        ]
        field_classes = {
            "nhs_number": NHSNumberField,
            "unique_reference_number": UniqueReferenceNumberField,
            "postcode": PostcodeField,
            "gp_practice_postcode": PostcodeField,
        }
        widgets = {
            "nhs_number": forms.TextInput(
                attrs={"class": TEXT_INPUT},
            ),
            "unique_reference_number": forms.TextInput(
                attrs={"class": TEXT_INPUT},
            ),
            "sex": forms.Select(),
            "date_of_birth": DateInput(),
            "postcode": forms.TextInput(attrs={"class": TEXT_INPUT}),
            "ethnicity": forms.Select(),
            "diabetes_type": forms.Select(),
            "diagnosis_date": DateInput(),
            "death_date": DateInput(),
            "immunotherapy_date": DateInput(),
            "immunotherapy_received": forms.Select(),
            "learning_disability_status": forms.Select(),
            "adhd_asd_status": forms.Select(),
            "gp_practice_ods_code": forms.TextInput(attrs={"class": TEXT_INPUT}),
            "gp_practice_postcode": forms.TextInput(attrs={"class": TEXT_INPUT}),
        }

    def __init__(self, *args, **kwargs):
        self.audit_period = kwargs.pop("audit_period", None)
        self.paediatric_diabetes_unit = kwargs.pop("paediatric_diabetes_unit", None)
        self.override_postcode = kwargs.pop("override_postcode", False)
        self.dataset_year = (
            self.audit_period.get_dataset_year() if self.audit_period else 2021
        )
        super().__init__(*args, **kwargs)
        self._init_fields_by_dataset_year()

    def _england_imd_year_for_audit_period(self) -> int | None:
        """Map NPDA dataset year to England IMD publication year for postcode lookup."""
        if not self.audit_period:
            return None

        return 2025 if self.audit_period.get_dataset_year() >= 2026 else 2019

    def _init_fields_by_dataset_year(self):
        """
        Initialize form fields based on the dataset year.
        """
        # Determine which patient fields should be presented for this dataset year
        if self.dataset_year == 2026:
            allowed_fields = list(PATIENT_FIELD_HEADINGS_2026.keys())
        else:
            # Future-proofing for other dataset years
            allowed_fields = list(PATIENT_FIELD_HEADINGS_2021.keys())

        # Keep any explicit extra form fields (non-model) plus allowed model fields
        extra_fields = {
            "date_leaving_service",
            "reason_leaving_service",
            "gp_practice_postcode",
            "unique_reference_number",
        }
        keep_fields = set(allowed_fields) | extra_fields

        # Remove fields that are not relevant to this dataset year
        for fname in list(self.fields.keys()):
            if fname not in keep_fields:
                del self.fields[fname]

        # Set help texts and labels dynamically from model field and headings
        for field_name in allowed_fields:
            if field_name not in self.fields:
                continue  # Skip if field is not present in the form
            # Set help text from model field
            # Set label from headings
            label = get_field_heading(field_name, self.dataset_year)
            note = get_field_notes(field_name, self.dataset_year)
            reference = get_field_justification_standard(field_name, self.dataset_year)
            self.fields[field_name].label = label
            self.fields[field_name].help_text = note
            self.fields[field_name].reference = reference

        PATIENT_CATEGORIES = (
            PATIENT_CATEGORIES_2021
            if self.dataset_year == 2021
            else PATIENT_CATEGORIES_2026
        )

        # Set initial values for transfer fields if editing an existing patient
        # and ensure we process categories in priority order
        sorted_categories = sorted(
            PATIENT_CATEGORIES, key=lambda c: c.get("priority", 0)
        )
        for category in sorted_categories:
            for field in category["fields"]:
                if field not in self.fields:
                    continue
                self.fields[field].category = category["name"]
                self.fields[field].category_colour = category["colour"]

        # Reorder form fields so they appear grouped by the category order
        # defined in PATIENT_CATEGORIES. We perform a stable sort based on
        # category priority and preserve the original relative order for any
        # fields that share the same priority or are uncategorised. This
        # avoids popping items from `self.fields` which can be error-prone
        # when the form is used in different contexts (UI vs CSV upload).
        from collections import OrderedDict

        # Record original order index for stability
        original_keys = list(self.fields.keys())
        original_index = {k: i for i, k in enumerate(original_keys)}

        # Build a map of field -> (priority, within_category_index)
        priority_map = {}
        within_index = {}
        for cat in sorted_categories:
            pr = cat.get("priority", 0)
            for idx, fname in enumerate(cat.get("fields", [])):
                # Lower priority value sorts earlier (1 is high priority)
                priority_map[fname] = pr
                within_index[fname] = idx

        # Define a key function that sorts by (priority, within_category_index, original_index)
        def sort_key(fname):
            return (
                priority_map.get(fname, 9999),
                within_index.get(fname, 9999),
                original_index.get(fname, 9999),
            )

        ordered_keys = sorted(original_keys, key=sort_key)

        new_fields = OrderedDict((k, self.fields[k]) for k in ordered_keys)

        # Replace the form's fields with the reordered mapping
        self.fields = new_fields

        # Populate transfer-related initial values if editing an existing patient
        if self.instance.pk:
            try:
                patient_transfer = Transfer.objects.filter(patient=self.instance).get()
                self.fields[
                    "date_leaving_service"
                ].initial = patient_transfer.date_leaving_service
                self.fields[
                    "reason_leaving_service"
                ].initial = patient_transfer.reason_leaving_service
            except Transfer.DoesNotExist:
                pass

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data["date_of_birth"]

        if date_of_birth:
            today = date.today()
            age = relativedelta(today, date_of_birth).years

            not_in_the_future_validator(date_of_birth)

            if age >= 25:
                raise ValidationError(
                    "NPDA patients cannot be 25+ years old. This patient is %(age)s",
                    params={"age": age},
                )

        return date_of_birth

    def clean_diagnosis_date(self):
        diagnosis_date = self.cleaned_data["diagnosis_date"]
        not_in_the_future_validator(diagnosis_date)

        return diagnosis_date

    def clean_death_date(self):
        death_date = self.cleaned_data["death_date"]
        not_in_the_future_validator(death_date)

        return death_date

    def clean_date_leaving_service(self):
        date_leaving_service = self.cleaned_data["date_leaving_service"]
        if date_leaving_service == "":
            return None
        elif date_leaving_service is not None:
            not_in_the_future_validator(date_leaving_service)
        return date_leaving_service

    def clean_reason_leaving_service(self):
        reason_leaving_service = self.cleaned_data["reason_leaving_service"]
        if reason_leaving_service == "":
            return None
        return reason_leaving_service

    def clean_adhd_asd_status(self):
        data = self.cleaned_data["adhd_asd_status"]
        # Convert the list of tuples to a dictionary
        adhd_asd_status_dict = dict(ADHD_ASD)
        if data is None or data in adhd_asd_status_dict:
            return data
        else:
            options = str(ADHD_ASD).strip("[]").replace(")", "").replace("(", "")
            raise ValidationError(
                f"'{data}' is not a value for 'ADHD/ASD Status'. Please select one of {options}."
            )

    def clean_learning_disability_status(self):
        data = self.cleaned_data["learning_disability_status"]
        # Convert the list of tuples to a dictionary
        learning_disability_status_dict = dict(YES_NO_UNKNOWN)
        if data is None or data in learning_disability_status_dict:
            return data
        else:
            options = str(YES_NO_UNKNOWN).strip("[]").replace(")", "").replace("(", "")
            raise ValidationError(
                f"'{data}' is not a value for 'Learning Disability Status'. Please select one of {options}."
            )

    def clean_immunotherapy_received(self):
        data = self.cleaned_data["immunotherapy_received"]
        # Convert the list of tuples to a dictionary
        yes_no_unknown_dict = dict(YES_NO_UNKNOWN)
        if data is None or data in yes_no_unknown_dict:
            return data
        else:
            options = str(YES_NO_UNKNOWN).strip("[]").replace(")", "").replace("(", "")
            raise ValidationError(
                f"'{data}' is not a value for 'Immunotherapy Received'. Please select one of {options}."
            )

    def handle_async_validation_result(self, key):
        value = getattr(self.async_validation_results, key)
        # override the invalid postcode error if the user has sanctioned the postcode
        if (
            key == "postcode"
            and type(value) is ValidationError
            and self.override_postcode
        ):
            postcode = self.cleaned_data["postcode"]
            if postcode:
                self.cleaned_data[key] = postcode
        else:
            if type(value) is ValidationError:
                self.add_error(key, value)
            elif value:
                self.cleaned_data[key] = value

    def clean(self):
        cleaned_data = self.cleaned_data
        date_of_birth = cleaned_data.get("date_of_birth")
        diagnosis_date = cleaned_data.get("diagnosis_date")
        death_date = cleaned_data.get("death_date")
        gp_practice_ods_code = cleaned_data.get("gp_practice_ods_code")
        gp_practice_postcode = cleaned_data.get("gp_practice_postcode")
        immunotherapy_date = cleaned_data.get("immunotherapy_date")
        immunotherapy_received = cleaned_data.get("immunotherapy_received")
        nhs_number = cleaned_data.get("nhs_number")
        unique_reference_number = cleaned_data.get("unique_reference_number")

        if not nhs_number and not unique_reference_number:
            self.add_error(
                "nhs_number",
                ValidationError(
                    "Either NHS Number or Unique Reference Number must be provided."
                ),
            )
            self.add_error(
                "unique_reference_number",
                ValidationError(
                    "Either NHS Number or Unique Reference Number must be provided."
                ),
            )

        if nhs_number and unique_reference_number:
            self.add_error(
                "nhs_number",
                ValidationError(
                    "Only one of NHS Number or Unique Reference Number can be provided."
                ),
            )

        # Synchronous invocation for npda platform UI vs async for csv_upload.
        if nhs_number or unique_reference_number:
            import asyncio

            if asyncio.iscoroutinefunction(self.validate_uniqueness):
                self._validate_field_uniqueness_async(
                    nhs_number, unique_reference_number
                )
            else:
                self.validate_uniqueness(nhs_number, unique_reference_number)

        reason_leaving_service = cleaned_data.get("reason_leaving_service")
        date_leaving_service = cleaned_data.get("date_leaving_service")
        if date_leaving_service and not reason_leaving_service:
            self.add_error(
                "reason_leaving_service",
                ValidationError(
                    "You must provide a reason for leaving the Paediatric Diabetes Unit"
                ),
            )
        if reason_leaving_service and not date_leaving_service:
            self.add_error(
                "date_leaving_service",
                ValidationError(
                    "You must provide a date for leaving the Paediatric Diabetes Unit"
                ),
            )
        if date_leaving_service is not None and date_of_birth is not None:
            if date_leaving_service < date_of_birth:
                self.add_error(
                    "date_leaving_service",
                    ValidationError(
                        "'Date Leaving Service' cannot be before 'Date of Birth'"
                    ),
                )

        if date_leaving_service is not None and diagnosis_date is not None:
            if date_leaving_service < diagnosis_date:
                self.add_error(
                    "date_leaving_service",
                    ValidationError(
                        "'Date Leaving Service' cannot be before 'Date of Diabetes Diagnosis'"
                    ),
                )

        if diagnosis_date is not None and date_of_birth is not None:
            if diagnosis_date < date_of_birth:
                self.add_error(
                    "diagnosis_date",
                    ValidationError(
                        "'Date of Diabetes Diagnosis' cannot be before 'Date of Birth'"
                    ),
                )

        if death_date is not None and date_of_birth is not None:
            if death_date < date_of_birth:
                self.add_error(
                    "death_date",
                    ValidationError("'Death Date' cannot be before 'Date of Birth'"),
                )

        if death_date is not None and diagnosis_date is not None:
            if death_date < diagnosis_date:
                self.add_error(
                    "death_date",
                    ValidationError(
                        "'Death Date' cannot be before 'Date of Diabetes Diagnosis'"
                    ),
                )

        if immunotherapy_date is not None and diagnosis_date is not None:
            if immunotherapy_date < diagnosis_date:
                self.add_error(
                    "immunotherapy_date",
                    ValidationError(
                        "'Date Immunotherapy Started' cannot be before 'Date of Diabetes Diagnosis'"
                    ),
                )

        if immunotherapy_date is not None and immunotherapy_date > date.today():
            self.add_error(
                "immunotherapy_date",
                ValidationError("'Date Immunotherapy Started' cannot be in the future"),
            )

        if immunotherapy_date is not None and date_of_birth is not None:
            if immunotherapy_date < date_of_birth:
                self.add_error(
                    "immunotherapy_date",
                    ValidationError(
                        "'Date Immunotherapy Started' cannot be before 'Date of Birth'"
                    ),
                )

        if immunotherapy_date is not None and death_date is not None:
            if immunotherapy_date > death_date:
                self.add_error(
                    "immunotherapy_date",
                    ValidationError(
                        "'Date Immunotherapy Started' cannot be after 'Death Date'"
                    ),
                )

        if (immunotherapy_date is not None and immunotherapy_received is None) or (
            immunotherapy_date is None
            and immunotherapy_received == YES_NO_UNKNOWN[0][0]
        ):
            self.add_error(
                "immunotherapy_date",
                ValidationError(
                    "'Immunotherapy Received' and 'Date Immunotherapy Started' must both be provided or both be empty"
                ),
            )
            self.add_error(
                "immunotherapy_received",
                ValidationError(
                    "'Immunotherapy Received' and 'Date Immunotherapy Started' must both be provided or both be empty"
                ),
            )

        if gp_practice_ods_code is None and gp_practice_postcode is None:
            self.add_error(
                "gp_practice_ods_code",
                ValidationError(
                    "'GP Practice ODS code' and 'GP Practice postcode' cannot both be empty"
                ),
            )

        if not getattr(self, "async_validation_results", None):
            self.async_validation_results = validate_patient_sync(
                postcode=self.cleaned_data["postcode"],
                gp_practice_ods_code=self.cleaned_data.get("gp_practice_ods_code"),
                gp_practice_postcode=self.cleaned_data.get("gp_practice_postcode"),
                england_imd_year=self._england_imd_year_for_audit_period(),
            )

        for key in [
            "postcode",
            "location_bng",
            "location_wgs84",
            "gp_practice_ods_code",
            "gp_practice_postcode",
        ]:
            self.handle_async_validation_result(key)

        return cleaned_data

    def save(self, commit=True):
        # We deliberately don't call super.save here as it throws ValueError on validation errors
        # and for CSV uploads we don't want that to stop us. As of Django 5.1.5 it doesn't do anything
        # else other than saving the model or setting up save_m2m. We don't use the latter so
        # I haven't implemented it here. The risk is that future versions of Django will add more
        # behaviour that we miss out on.

        self.instance.index_of_multiple_deprivation_quintile = (
            self.async_validation_results.index_of_multiple_deprivation_quintile
        )

        self.instance.location_bng = self.async_validation_results.location_bng
        self.instance.location_wgs84 = self.async_validation_results.location_wgs84

        if commit:
            self.instance.save()
            if Transfer.objects.filter(patient=self.instance).exists():
                patient_transfer = Transfer.objects.get(patient=self.instance)
                patient_transfer.date_leaving_service = self.cleaned_data[
                    "date_leaving_service"
                ]
                patient_transfer.reason_leaving_service = self.cleaned_data[
                    "reason_leaving_service"
                ]
                patient_transfer.previous_pz_code = (
                    patient_transfer.paediatric_diabetes_unit.pz_code
                )  # set previous_pz_code to the current PZ code
                patient_transfer.save()

        return self.instance

    async def validate_uniqueness_async(self, nhs_number, unique_reference_number):
        """
        Validate that the NHS Number or Unique Reference Number is unique within this submission.
        Handles both synchronous and asynchronous contexts.
        """
        if nhs_number:
            await self._validate_field_uniqueness_async(
                nhs_number,
                "nhs_number",
                "patient__nhs_number",
                "A child with this NHS Number already exists in this submission.",
            )

        if unique_reference_number:
            await self._validate_field_uniqueness_async(
                unique_reference_number,
                "unique_reference_number",
                "patient__unique_reference_number",
                "A child with this Unique Reference Number already exists in this submission.",
            )

    async def _validate_field_uniqueness_async(
        self, value, field_name, filter_field, error_message
    ):
        PatientSubmission = apps.get_model("npda", "PatientSubmission")

        @database_sync_to_async
        def get_submissions_count(filter_kwargs, exclude_kwargs):
            return (
                PatientSubmission.objects.filter(**filter_kwargs)
                .exclude(**exclude_kwargs)
                .count()
            )

        filter_kwargs = {
            "submission__submission_active": True,
            "submission__audit_period": self.audit_period,
            filter_field: value,
            "submission__paediatric_diabetes_unit": self.paediatric_diabetes_unit,
        }

        exclude_kwargs = {}

        if self.instance:
            exclude_kwargs["patient__pk"] = self.instance.pk

        count = await get_submissions_count(filter_kwargs, exclude_kwargs)

        if count > 0:
            self.add_error(field_name, ValidationError(error_message))

    def validate_uniqueness(self, nhs_number, unique_reference_number):
        """
        Validate that the NHS Number or Unique Reference Number is unique within this submission.
        Handles both synchronous and asynchronous contexts.
        """
        if nhs_number:
            self._validate_field_uniqueness(
                value=nhs_number,
                field_name="nhs_number",
                filter_field="patient__nhs_number",
                error_message="A child with this NHS Number already exists in this submission.",
            )

        if unique_reference_number:
            self._validate_field_uniqueness(
                value=unique_reference_number,
                field_name="unique_reference_number",
                filter_field="patient__unique_reference_number",
                error_message="A child with this Unique Reference Number already exists in this submission.",
            )

    def _validate_field_uniqueness(
        self, value, field_name, filter_field, error_message
    ):
        PatientSubmission = apps.get_model("npda", "PatientSubmission")

        def get_submissions_count(filter_kwargs, exclude_kwargs):
            return (
                PatientSubmission.objects.filter(**filter_kwargs)
                .exclude(**exclude_kwargs)
                .count()
            )

        filter_kwargs = {
            "submission__submission_active": True,
            "submission__audit_period": self.audit_period,
            filter_field: value,
            "submission__paediatric_diabetes_unit": self.paediatric_diabetes_unit,
        }

        exclude_kwargs = {}

        if self.instance:
            exclude_kwargs["patient__pk"] = self.instance.pk

        count = get_submissions_count(filter_kwargs, exclude_kwargs)

        if count > 0:
            self.add_error(field_name, ValidationError(error_message))
