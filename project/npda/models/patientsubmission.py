from typing import Iterable
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings


class PatientSubmission(models.Model):
    """
    The Submission class.

    This class is used to define the audit submission of patients that are being audited. The model tracks which audit year and quarter the submission relates to
    and the PZ code of the Paediatric Diabetes Unit that is conducting the audit.
    Each submission comprises  a list of unique patients and their visits as well as the csv file as a BinaryField.
    """

    patient = models.ForeignKey(
        on_delete=models.CASCADE,
        to="npda.Patient",
    )

    submission = models.ForeignKey(
        on_delete=models.CASCADE,
        to="npda.Submission",
    )

    class Meta:
        verbose_name = "PatientSubmission"
        verbose_name_plural = "PatientSubmissions"
        unique_together = ["patient", "submission"]

    def __str__(self) -> str:
        return f"{self.submission} for {self.patient}"

    def validate_unique_nhs_number(self, patient):
        """
        Check that the patient does not already exist in the submission
        """
        if self.submission.patients.filter(nhs_number=patient.nhs_number).exists():
            raise ValidationError(
                f"Patient with NHS number {patient.nhs_number} already exists in this submission"
            )

    def validate_unique_patient(self, patient):
        """
        Check that the patient does not already exist in the submission
        """
        if self.submission.patients.filter(pk=patient.pk).exists():
            raise ValidationError(
                f"Patient with id {patient.pk} already exists in this submission"
            )

    def save(self, args, kwargs) -> None:
        self.validate_unique_nhs_number(self.patient)
        return super().save(args, kwargs)
