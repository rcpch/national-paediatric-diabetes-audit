from django.db import models
from django.core.exceptions import ValidationError


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

    csv_file = models.FileField(
        upload_to="submissions/csv/",
        help_text="CSV file containing the audit data for this submission",
        default="submissions/csv/default.csv",
    )

    patients = models.ManyToManyField(to="npda.Patient", related_name="submissions")

    paediatric_diabetes_unit = models.ForeignKey(
        on_delete=models.CASCADE,
        to="npda.PaediatricDiabetesUnit",
        related_name="pdu_submissions",
    )

    def __str__(self) -> str:
        return f"{self.audit_year}, {self.patients.count()} patients"

    class Meta:
        verbose_name = "Submission"
        verbose_name_plural = "Submissions"
        ordering = ("audit_year",)

    def delete(self, *args, **kwargs):
        if self.submission_active:
            raise ValidationError("Cannot delete an active submission.")
        super().delete(*args, **kwargs)
