from django.core.exceptions import ValidationError
from django.db import models



class SubmissionManager(models.Manager):
    def get_submission_for_request(self, pdu, audit_period):
        return self.filter(
            audit_period=audit_period,
            paediatric_diabetes_unit=pdu,
            submission_active=True,
        ).first()


class Submission(models.Model):
    """
    The Submission class.

    This class is used to define the audit submission of patients that are being audited. The model tracks which audit year and quarter the submission relates to
    and the PZ code of the Paediatric Diabetes Unit that is conducting the audit.
    Each submission comprises  a list of unique patients and their visits as well as the csv file as a BinaryField.
    """

    objects = SubmissionManager()

    # This was the original field before audit_period was introduced. It remains for compatibility.
    audit_year = models.IntegerField(
        "Audit year",
        blank=False,
        null=False,
        help_text="Year the audit is being conducted",
    )

    audit_period = models.ForeignKey(
        on_delete=models.RESTRICT,
        to="npda.AuditPeriod",
        null=True,  # for compatibility as we migrate from the old audit_year field
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
        on_delete=models.RESTRICT,
        to="npda.NPDAUser",
    )

    csv_file = models.BinaryField(
        help_text="CSV file containing the audit data for this submission",
        null=True,  # submissions that are not active will have their csv file deleted
    )

    csv_file_name = models.CharField(
        "CSV file name",
        help_text="Name of the uploaded CSV file",
        null=True,
        blank=True,
    )

    errors = models.JSONField(
        "Errors",
        help_text="Errors that have been found in the uploaded CSV file",
        null=True,
        blank=True,
    )

    total_unique_patients = models.IntegerField(
        "Total unique patients",
        help_text="Total number of unique patients in this submission",
        null=True,
        blank=True,
    )

    visit_counts_per_patient = models.JSONField(
        "Visit counts per patient",
        help_text="Counts of visits per patient in this submission",
        null=True,
        blank=True,
    )

    total_unique_visits = models.IntegerField(
        "Total unique visits",
        help_text="Total number of unique visits in this submission",
        null=True,
        blank=True,
    )

    patients = models.ManyToManyField(
        to="npda.Patient", through="npda.PatientSubmission", related_name="submissions"
    )

    paediatric_diabetes_unit = models.ForeignKey(
        on_delete=models.CASCADE,
        to="npda.PaediatricDiabetesUnit",
        related_name="pdu_submissions",
    )

    def __str__(self) -> str:
        return f"Submission from {self.paediatric_diabetes_unit} for {self.audit_period or self.audit_year}"

    class Meta:
        verbose_name = "Submission"
        verbose_name_plural = "Submissions"
        ordering = ("audit_year",)

    def delete(self, *args, **kwargs):
        if self.submission_active:
            raise ValidationError("Cannot delete an active submission.")
        super().delete(*args, **kwargs)
