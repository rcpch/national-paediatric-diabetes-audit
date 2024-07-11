from datetime import date
from typing import Any, Iterable
from django.db import models

from project.npda.general_functions.quarter_for_date import retrieve_quarter_for_date


class AuditCohort(models.Model):
    """
    The AuditCohort class.

    This class is used to define the cohort of patients that are being audited. The cohort tracks the progress of the audit
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

    pz_code = models.CharField(
        "PZ code",
        max_length=10,
        blank=False,
        null=False,
        help_text="The PZ code of the Paediatric Diabetes Unit",
    )

    ods_code = models.CharField(
        "PZ code",
        max_length=10,
        blank=False,
        null=False,
        help_text="The ODS code of the Organisation",
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

    submission_approved = models.BooleanField(
        "Submission approved",
        default=False,
        help_text="Submission has been approved for inclusion in the audit",
    )

    patients = models.ManyToManyField(to="npda.Patient", related_name="audit_cohorts")

    def __str__(self) -> str:
        return f"{self.audit_year} ({self.quarter}), {self.patients.count()} patients"

    def save(self, *args, **kwargs) -> None:
        self.audit_year = int(self.submission_date.year)
        self.quarter = retrieve_quarter_for_date(self.submission_date.date())
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Audit Cohort"
        verbose_name_plural = "Audit Cohorts"
        ordering = ("audit_year", "quarter")
