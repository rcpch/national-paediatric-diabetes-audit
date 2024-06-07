from datetime import date
from typing import Any, Iterable
from django.db import models


class AuditCohort(models.Model):
    """
    The AuditCohort class.

    This class is used to define the cohort of patients that are being audited. The cohort tracks the progress of the audit
    """

    data_uploaded_date = models.DateTimeField(
        "Date data uploaded", auto_now_add=True, help_text="Date the data was uploaded"
    )

    submission_valid = models.BooleanField(
        "Data validated",
        default=True,
        help_text="Data is earmarked for inclusion in the audit",
    )

    patient = models.ForeignKey(
        "npda.Patient",
        on_delete=models.CASCADE,
        related_name="patients_audit_cohorts",
        help_text="Patient being audited",
    )

    audit_year = models.IntegerField(
        "Audit year",
        blank=False,
        null=False,
        help_text="Year the audit is being conducted",
    )

    cohort_number = models.IntegerField(
        "Cohort number",
        blank=False,
        null=False,
        help_text="The cohort number of the patient",
    )

    def calculate_cohort_number(self):
        """
        Returns the cohort number of the patient

        **The audit year starts on the 1st of April and ends on the 31st of March the following year**
        Returns 1 if the patient has less than 25% of the audit year remaining
        Returns 2 if the patient has less than 50% of the audit year remaining
        Returns 3 if the patient has less than 75% of the audit year remaining
        Returns 4 if the patient has more than 75% of the audit year remaining
        """
        audit_start_date = date(self.audit_year, 4, 1)
        if self.data_uploaded_date.date() < audit_start_date:
            # The patient was audited in the previous year
            days_remaining = (audit_start_date - self.data_uploaded_date.date()).days
        else:
            # The patient was audited in the current year
            audit_end_date = date(self.audit_year + 1, 3, 31)
            days_remaining = (audit_start_date - self.data_uploaded_date.date()).days
        total_days = (audit_end_date - audit_start_date).days
        completed_days = total_days - days_remaining
        if (days_remaining / completed_days) < 0.25:
            return 1
        elif (days_remaining / completed_days) < 0.5:
            return 2
        elif (days_remaining / completed_days) < 0.75:
            return 3
        else:
            return 4

    def __str__(self) -> str:
        return (
            f"{self.patient}, {self.visit}, {self.audit_year}, {self.cohort_number()}"
        )

    def save(self, *args, **kwargs) -> None:
        self.audit_year = int(self.data_uploaded_date.year)
        cohort_number = self.calculate_cohort_number()
        self.cohort_number = cohort_number
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Audit Cohort"
        verbose_name_plural = "Audit Cohorts"
        ordering = ("patient", "audit_year", "cohort_number")
