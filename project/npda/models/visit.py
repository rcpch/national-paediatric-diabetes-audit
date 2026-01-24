# python imports
from datetime import date
import logging
from decimal import Decimal

# django imports
from django.contrib.gis.db import models

# npda imports
from .help_text_mixin import HelpTextMixin
from .categorised_formfield_mixin import *
from ...constants import (
    ALL_VISIT_DATES,
    ALBUMINURIA_STAGES,
    CLOSED_LOOP_TYPES,
    DKA_ADDITIONAL_THERAPIES,
    GLUCOSE_MONITORING_TYPES,
    HBA1C_FORMATS,
    HOSPITAL_ADMISSION_REASONS,
    INSULIN_TREATMENT,
    NON_INSULIN_TREATMENT,
    PSYCHOLOGICAL_SUPPORT_OUTCOMES,
    RETINAL_SCREENING_RESULTS,
    SMOKING_STATUS,
    SMOKING_VAPING_STATUS,
    THYROID_TREATMENT_STATUS,
    TREATMENT_TYPES,
    YES_NO_UNKNOWN,
)

from project.npda.general_functions.headings import get_field_heading
from project.npda.general_functions.justification_or_standard import (
    get_field_notes,
    get_field_justification_standard,
)

logger = logging.getLogger(__name__)


class Visit(models.Model):
    visit_date = CategorisedDateField(
        null=True,
        blank=True,
        default=None,
    )

    height = CategorisedDecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        default=None,
        category="Measurements",
    )

    height_centile = CategorisedDecimalField(
        verbose_name="Height Centile",
        help_text="This is a calculated field. Centile value for height if available. If not available, can be blank.",
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        default=None,
        category="Measurements",
    )

    height_sds = CategorisedDecimalField(
        verbose_name="Height SDS",
        help_text="This is a calculated field. Centile value for height if available. If not available, can be blank.",
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        default=None,
        category="Measurements",
    )

    weight = CategorisedDecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        default=None,
        category="Measurements",
    )

    weight_centile = CategorisedDecimalField(
        verbose_name="Weight Centile",
        help_text="This is a calculated field. Centile value for weight if available. If not available, can be blank.",
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        default=None,
        category="Measurements",
    )

    weight_sds = CategorisedDecimalField(
        verbose_name="Weight SDS",
        help_text="This is a calculated field. Centile value for weight if available. If not available, can be blank.",
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        default=None,
        category="Measurements",
    )

    bmi = CategorisedDecimalField(
        verbose_name="Body Mass Index",
        help_text="This is a calculated field. BMI value for the patient. BMI health check is only completed if both height and weight is measured at the same visit",
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        default=None,
        category="Measurements",
    )

    bmi_centile = CategorisedDecimalField(
        verbose_name="Body Mass Index Centile",
        help_text="This is a calculated field. Centile value for height if available. If not available, can be blank.",
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        default=None,
        category="Measurements",
    )

    bmi_sds = CategorisedDecimalField(
        verbose_name="Body Mass Index SDS",
        help_text="This is a calculated field. Centile value for body mass index if height and weight are available. If not available, can be blank.",
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        default=None,
        category="Measurements",
    )

    height_weight_observation_date = CategorisedDateField(
        null=True,
        blank=True,
        default=None,
        category="Measurements",
    )

    hba1c = CategorisedDecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        default=None,
        category="HBA1c",
    )

    hba1c_format = CategorisedPositiveSmallIntegerField(
        choices=HBA1C_FORMATS,
        null=True,
        blank=True,
        default=None,
        category="HBA1c",
    )

    hba1c_date = CategorisedDateField(
        null=True,
        blank=True,
        default=None,
        category="HBA1c",
    )

    treatment = CategorisedPositiveSmallIntegerField(
        choices=TREATMENT_TYPES,
        null=True,
        blank=True,
        default=None,
        category="Treatment",
    )

    closed_loop_system = CategorisedPositiveSmallIntegerField(
        choices=CLOSED_LOOP_TYPES,
        null=True,
        blank=True,
        default=None,
        category="Treatment",
    )

    glucose_monitoring = CategorisedPositiveSmallIntegerField(
        choices=GLUCOSE_MONITORING_TYPES,
        null=True,
        blank=True,
        default=None,
        category="CGM",
    )

    systolic_blood_pressure = CategorisedIntegerField(
        null=True,
        blank=True,
        default=None,
        category="BP",
    )

    diastolic_blood_pressure = CategorisedIntegerField(
        null=True,
        blank=True,
        default=None,
        category="BP",
    )

    blood_pressure_observation_date = CategorisedDateField(
        null=True,
        blank=True,
        default=None,
        category="BP",
    )

    foot_examination_observation_date = CategorisedDateField(
        null=True,
        blank=True,
        default=None,
        category="Foot Care",
    )

    retinal_screening_observation_date = CategorisedDateField(
        null=True,
        blank=True,
        default=None,
        category="DECS",
    )

    retinal_screening_result = CategorisedPositiveSmallIntegerField(
        choices=RETINAL_SCREENING_RESULTS,
        null=True,
        blank=True,
        default=None,
        category="DECS",
    )

    albumin_creatinine_ratio = CategorisedDecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        default=None,
        category="ACR",
    )

    albumin_creatinine_ratio_date = CategorisedDateField(
        null=True,
        blank=True,
        default=None,
        category="ACR",
    )

    albuminuria_stage = CategorisedPositiveSmallIntegerField(
        choices=ALBUMINURIA_STAGES,
        null=True,
        blank=True,
        default=None,
        category="ACR",
    )

    total_cholesterol = CategorisedDecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        default=None,
        category="Cholesterol",
    )

    total_cholesterol_date = CategorisedDateField(
        null=True,
        blank=True,
        default=None,
        category="Cholesterol",
    )

    thyroid_function_date = CategorisedDateField(
        null=True,
        blank=True,
        default=None,
        category="Thyroid",
    )

    thyroid_treatment_status = CategorisedPositiveSmallIntegerField(
        choices=THYROID_TREATMENT_STATUS,
        null=True,
        blank=True,
        default=None,
        category="Thyroid",
    )

    coeliac_screen_date = CategorisedDateField(
        null=True,
        blank=True,
        default=None,
        category="Coeliac",
    )

    gluten_free_diet = CategorisedPositiveSmallIntegerField(
        choices=YES_NO_UNKNOWN,
        null=True,
        blank=True,
        default=None,
        category="Coeliac",
    )

    psychological_screening_assessment_date = CategorisedDateField(
        null=True,
        blank=True,
        default=None,
        category="Psychology",
    )

    psychological_additional_support_status = CategorisedPositiveSmallIntegerField(
        choices=YES_NO_UNKNOWN,
        null=True,
        blank=True,
        default=None,
        category="Psychology",
    )

    smoking_status = CategorisedPositiveSmallIntegerField(
        choices=SMOKING_STATUS,
        null=True,
        blank=True,
        default=None,
        category="Smoking",
    )

    smoking_cessation_referral_date = CategorisedDateField(
        null=True,
        blank=True,
        default=None,
        category="Smoking",
    )

    carbohydrate_counting_level_three_education_date = CategorisedDateField(
        null=True,
        blank=True,
        default=None,
        category="Dietician",
    )

    dietician_additional_appointment_offered = CategorisedPositiveSmallIntegerField(
        choices=YES_NO_UNKNOWN,
        null=True,
        blank=True,
        default=None,
        category="Dietician",
    )

    dietician_additional_appointment_date = CategorisedDateField(
        null=True,
        blank=True,
        default=None,
        category="Dietician",
    )

    flu_immunisation_recommended_date = CategorisedDateField(
        null=True,
        blank=True,
        default=None,
        category="Immunisation (flu)",
    )

    ketone_meter_training = CategorisedPositiveSmallIntegerField(
        choices=YES_NO_UNKNOWN,
        null=True,
        blank=True,
        default=None,
        category="Sick Day Rules",
    )

    sick_day_rules_training_date = CategorisedDateField(
        null=True,
        blank=True,
        default=None,
        category="Sick Day Rules",
    )

    hospital_admission_date = CategorisedDateField(
        null=True,
        blank=True,
        default=None,
        category="Hospital Admission",
    )

    hospital_discharge_date = CategorisedDateField(
        null=True,
        blank=True,
        default=None,
        category="Hospital Admission",
    )

    hospital_admission_reason = CategorisedPositiveSmallIntegerField(
        choices=HOSPITAL_ADMISSION_REASONS,
        null=True,
        blank=True,
        default=None,
        category="Hospital Admission",
    )

    dka_additional_therapies = CategorisedPositiveSmallIntegerField(
        choices=DKA_ADDITIONAL_THERAPIES,
        null=True,
        blank=True,
        default=None,
        category="Hospital Admission",
    )

    hospital_admission_other = CategorisedCharField(
        max_length=500,
        null=True,
        blank=True,
        default=None,
        category="Hospital Admission",
    )

    # additional 2026 fields
    smoking_vaping_status = CategorisedPositiveSmallIntegerField(
        null=True,
        blank=True,
        default=None,
        choices=SMOKING_VAPING_STATUS,
        category="Smoking",
    )

    immunotherapy_received = CategorisedPositiveSmallIntegerField(
        null=True,
        blank=True,
        default=None,
        choices=YES_NO_UNKNOWN,
        category="Treatment",
    )

    immunotherapy_date = CategorisedDateField(
        null=True,
        blank=True,
        default=None,
        category="Treatment",
    )

    blood_gas_ph = CategorisedDecimalField(
        null=True,
        blank=True,
        default=None,
        max_digits=4,
        decimal_places=3,
        category="Hospital Admission",
    )

    blood_gas_bicarbonate = CategorisedDecimalField(
        null=True,
        blank=True,
        default=None,
        max_digits=5,
        decimal_places=2,
        category="Hospital Admission",
    )

    insulin_regimen = CategorisedPositiveSmallIntegerField(
        null=True,
        blank=True,
        default=None,
        choices=INSULIN_TREATMENT,
        category="Treatment",
    )

    non_insulin_medication = CategorisedPositiveSmallIntegerField(
        null=True,
        blank=True,
        default=None,
        choices=NON_INSULIN_TREATMENT,
        category="Treatment",
    )

    dietary_lifestyle_modification = CategorisedPositiveSmallIntegerField(
        null=True,
        blank=True,
        default=None,
        choices=YES_NO_UNKNOWN,
        category="Treatment",
    )

    cgm_use = CategorisedPositiveSmallIntegerField(
        null=True,
        blank=True,
        default=None,
        choices=YES_NO_UNKNOWN,
        category="CGM",
    )

    psychological_support_outcome = CategorisedPositiveSmallIntegerField(
        null=True,
        blank=True,
        default=None,
        choices=PSYCHOLOGICAL_SUPPORT_OUTCOMES,
        category="Psychological Support",
    )

    # validation fields

    is_valid = models.BooleanField(
        verbose_name="Record is valid", blank=True, null=True, default=False
    )

    errors = models.JSONField(
        verbose_name="Validation errors", blank=True, null=True, default=None
    )

    dataset_year = models.PositiveSmallIntegerField(
        verbose_name="Dataset Year",
        default=2021,
        help_text="The dataset year used for this patient.",
    )

    # relationships

    patient = models.ForeignKey(to="npda.Patient", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Visit"
        verbose_name_plural = "Visits"
        ordering = ("-visit_date",)

    def __str__(self) -> str:
        return f"Patient visit for {self.patient} on {self.visit_date}"

    def _hba1c_mmol_mol(self):
        """
        Return HbA1c in mmol/mol

        If has been supplied in %, convert to mmol/mol using the formula
        HbA1c (%) = (0.09148 * HbA1c (mmol/mol)) + 2.152
        HbA1c (mmol/mol) = (HbA1c (%) - 2.152) / 0.09148
        """

        if (
            self.hba1c_format is not None
            and self.hba1c is not None
            and (
                (self.hba1c > 2 and self.hba1c_format == HBA1C_FORMATS[1][0])
                or (self.hba1c >= 9 and self.hba1c_format == HBA1C_FORMATS[0][0])
            )
        ):
            if self.hba1c_format == HBA1C_FORMATS[0][0]:  # mmol/mol
                return self.hba1c
            elif self.hba1c_format == HBA1C_FORMATS[1][0]:
                # Convert self.hba1c to Decimal before performing the calculation
                hba1c_decimal = Decimal(str(self.hba1c))
                result = (hba1c_decimal - Decimal("2.152")) / Decimal("0.09148")
                return int(
                    result.quantize(Decimal("1"), rounding="ROUND_HALF_UP")
                )  # or ROUND_HALF_EVEN, etc.

        return None

    def get_field_label(self, field_name):
        """Get year-appropriate label for any field."""
        return get_field_heading(field_name, self.dataset_year)

    def get_field_help_text(self, field_name):
        """Get year-appropriate help text for any field."""
        return get_field_notes(field_name, self.dataset_year)

    def get_field_justification_or_standard(self, field_name):
        """Get year-appropriate justification or standard for any field."""
        return get_field_justification_standard(field_name, self.dataset_year)
