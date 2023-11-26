# python imports

# django imports
from django.contrib.gis.db import models
from django.contrib.gis.db.models import (
    DateField,
    PositiveSmallIntegerField,
    ForeignKey,
)

# npda imports
from ...constants import LEAVE_PDU_REASONS


class Site(models.Model):
    date_leaving_service = DateField(verbose_name="Date of leaving service")

    date_leaving_service = DateField(verbose_name="Date of leaving service")

    reason_leaving_service = PositiveSmallIntegerField(
        verbose_name="Reason for leaving service", choices=LEAVE_PDU_REASONS
    )

    # relationships
    pdu = ForeignKey(to="npda.PaediatricDiabetesUnit", on_delete=models.CASCADE)

    patient = ForeignKey(to="npda.Patient", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Site"
        verbose_name_plural = "Sites"

    def __str__(self) -> str:
        return f"{self.patient} at {self.pdu}"
