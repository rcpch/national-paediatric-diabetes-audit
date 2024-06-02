# python imports

# django imports
from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db import models
from django.contrib.gis.db.models import (
    DateField,
    PositiveSmallIntegerField,
    ForeignKey,
)
from ...constants import *

# npda imports
from ...constants import (
    LEAVE_PDU_REASONS,
    CAN_ALLOCATE_NPDA_LEAD_CENTRE,
    CAN_DELETE_NPDA_LEAD_CENTRE,
    CAN_EDIT_NPDA_LEAD_CENTRE,
    CAN_TRANSFER_NPDA_LEAD_CENTRE,
)


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
    paediatric_diabetes_unit_pz_code = models.CharField(
        _("PZ Code"),
        help_text=_("Enter the PZ Code"),
        max_length=150,
        null=True,
        blank=True,
    )

    organisation_ods_code = models.CharField(
        _("Organisation ODS Code"),
        help_text=_("Enter the Organisation ODS Code"),
        max_length=150,
        null=True,
        blank=True,
    )

    patient = ForeignKey(to="npda.Patient", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Site"
        verbose_name_plural = "Sites"
        permissions = [
            CAN_ALLOCATE_NPDA_LEAD_CENTRE,
            CAN_DELETE_NPDA_LEAD_CENTRE,
            CAN_EDIT_NPDA_LEAD_CENTRE,
            CAN_TRANSFER_NPDA_LEAD_CENTRE,
        ]

    def __str__(self) -> str:
        return f"{self.patient} at {self.organisation_ods_code}({self.paediatric_diabetes_unit_pz_code})"
