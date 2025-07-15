from django.contrib.gis.db import models
from django.core.exceptions import PermissionDenied


class PaediatricDiabetesUnitManager(models.Manager):
    def get_audit_period_for_request(self, request, *args, **kwargs):
        can_view_all_data = request.user.is_superuser or request.user.is_rcpch_audit_team_member

        if "pz_code" in kwargs:
            try:
                pdu = PaediatricDiabetesUnit.objects.get(pz_code=kwargs["pz_code"])
            except PaediatricDiabetesUnit.DoesNotExist as e:
                if not can_view_all_data:
                    raise PermissionDenied(f"PDU {kwargs['pz_code']} does not exist")

                raise e
        else:
            pdu = PaediatricDiabetesUnit.objects.get(pz_code=request.session["pz_code"])

        if not can_view_all_data:
            can_view_this_pdu = request.user.organisation_employers.filter(
                pz_code=pdu.pz_code
            ).exists()

            if not can_view_this_pdu:
                raise PermissionDenied(
                    f"User {request.user} does not have permission to view PDU {pdu.pz_code}"
                )
        
        return pdu


class PaediatricDiabetesUnit(models.Model):
    """
    This model stores the paediatric diabetes unit reference PZ code and ODS code of the associated organisation
    """

    objects = PaediatricDiabetesUnitManager()

    pz_code = models.CharField(
        max_length=10,
        help_text="Enter the paediatric diabetes unit PZ code",
    )
    lead_organisation_ods_code = models.CharField(
        max_length=10,
        help_text="Enter the organisation ODS code",
    )
    # NB: since 15/07/2025 this is populated from the "name" field in the API, not the name of the lead organisation
    #  - https://github.com/rcpch/rcpch-nhs-organisations/pull/109
    #  - https://github.com/rcpch/rcpch-nhs-organisations/pull/110
    lead_organisation_name = models.CharField(
        max_length=75,
        help_text="Enter the organisation name",
        blank=True,
        null=True,
    )
    lead_organisation_geocoordinates = models.PointField(
        help_text="Enter the organisation geocoordinates",
        blank=True,
        null=True,
    )
    parent_ods_code = models.CharField(
        max_length=10,
        help_text="Enter the parent ODS code",
        blank=True,
        null=True,
    )
    parent_name = models.CharField(
        max_length=75,
        help_text="Enter the parent name",
        blank=True,
        null=True,
    )
    paediatric_diabetes_network_code = models.CharField(
        max_length=10,
        help_text="Enter the paedidatric diabetes network PN code",
        blank=True,
        null=True,
    )
    paediatric_diabetes_network_name = models.CharField(
        max_length=75,
        help_text="Enter the paediatric diabetes network name",
        blank=True,
        null=True,
    )
    active = models.BooleanField(
        default=True,
        help_text="Is the PDU active?",
    )
    last_updated = models.DateTimeField(
        help_text="Last updated date",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Paediatric Diabetes Unit"
        verbose_name_plural = "Paediatric Diabetes Units"

    def __str__(self):
        return self.pz_code
