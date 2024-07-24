from django.contrib.gis.db import models


class PaediatricDiabetesUnit(models.Model):
    """
    This model stores the paediatric diabetes unit reference PZ code and ODS code of the associated organisation
    """

    pz_code = models.CharField(
        max_length=10,
        help_text="Enter the paediatric diabetes unit PZ code",
        unique=True,
    )
    ods_code = models.CharField(
        max_length=10,
        help_text="Enter the organisation ODS code",
        unique=True,
    )

    class Meta:
        verbose_name = "Paediatric Diabetes Unit"
        verbose_name_plural = "Paediatric Diabetes Units"
