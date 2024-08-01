from datetime import date
from typing import Any, Iterable
from django.db import models

from project.npda.general_functions.quarter_for_date import retrieve_quarter_for_date


class Submission(models.Model):
    """
    The Submission class.

    This class is used to define the audit submission of patients that are being audited. The model tracks which audit year and quarter the submission relates to
    and the PZ code of the Paediatric Diabetes Unit that is conducting the audit.
    Each submission comprises  a list of unique patients and their visits as well as the csv file as a BinaryField.
    """

    audit_year = models.IntegerField(
        "Audit year",
        blank=False,
        null=False,
        help_text="Year the audit is being conducted",
    )

    quarter = models.IntegerField(
        "Quarter",
        blank=False,
        null=False,
        help_text="The quarter in the audit year of the patient",
    )

    submission_date = models.DateTimeField(
        "Submission date",
        help_text="Date the submission was created",
    )

    submission_active = models.BooleanField(
        "Submission active",
        default=True,
        help_text="Submission is active and being considered for inclusion in the audit",
    )

    submission_by = models.ForeignKey(
        on_delete=models.CASCADE,
        to="npda.NPDAUser",
    )

    patients = models.ManyToManyField(to="npda.Patient", related_name="submissions")

    paediatric_diabetes_unit = models.ForeignKey(
        on_delete=models.CASCADE,
        to="npda.PaediatricDiabetesUnit",
        related_name="pdu_submissions",
    )

    def __str__(self) -> str:
        return f"{self.audit_year} ({self.quarter}), {self.patients.count()} patients"

    class Meta:
        verbose_name = "Submission"
        verbose_name_plural = "Submissions"
        ordering = ("audit_year", "quarter")
