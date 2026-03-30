from django.db import models


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

    def __str__(self) -> str:
        return f"{self.submission} for {self.patient}"
