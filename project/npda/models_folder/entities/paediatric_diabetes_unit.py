# python imports

# django imports
from django.contrib.gis.db import models
from django.db.models import CharField


class PaediatricDiabetesUnit(models.Model):
    pdu_number = CharField("Paediatric Diabetes Unit PZ Number", max_length=5)
    # pdu_name = CharField(verbose_name="Paediatric Diabetes Unit Name", max_length=100)
    nhs_england_region = models.ForeignKey(
        to="npda.NHSEnglandRegion", on_delete=models.CASCADE
    )

    organisation = models.ForeignKey(to="npda.Organisation", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Paediatric Diabetes Unit"
        verbose_name_plural = "Paediatric Diabetes Units"
        ordering = ("pdu_number",)

    def __str__(self) -> str:
        return self.organisation
