# python imports

# django imports
from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db import models
from django.contrib.gis.db.models import (
    DateField,
    PositiveSmallIntegerField,
    ForeignKey,
)

# npda imports
from ...constants import LEAVE_PDU_REASONS


class Site(models.Model):
    date_leaving_service = DateField(
        verbose_name="Date of leaving service", blank=True, null=True
    )

    reason_leaving_service = PositiveSmallIntegerField(
        verbose_name="Reason for leaving service",
        choices=LEAVE_PDU_REASONS,
        blank=True,
        null=True,
    )

    # relationships
    pdu = models.CharField(
        _("PZ Code"),
        help_text=_("Enter the PZ Code"),
        max_length=150,
        null=True,
        blank=True,
    )

    patient = ForeignKey(to="npda.Patient", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Site"
        verbose_name_plural = "Sites"

    def __str__(self) -> str:
        return f"{self.patient} at {self.pdu}"
