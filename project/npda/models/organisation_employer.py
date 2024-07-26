from django.contrib.gis.db.models import Model, BooleanField, CASCADE, ForeignKey
from django.utils.translation import gettext_lazy as _


class OrganisationEmployer(Model):
    """
    This model is the link table between the NPDAUser and the PaediatricDiabetesUnit models
    Rather than having a many-to-many relationship between the two models, we have a link table as we need to store
    information about the user's role within the unit
    """

    is_primary_employer = BooleanField(
        default=True,
        help_text="Is this the user's primary employer?",
    )

    class Meta:
        verbose_name = "Organisation Employer"
        verbose_name_plural = "Organisation Employers"

    def __str__(self):
        return f"{self.paediatric_diabetes_unit} for {self.npda_user}"

    paediatric_diabetes_unit = ForeignKey(
        to="npda.PaediatricDiabetesUnit",
        on_delete=CASCADE,
        related_name="npda_users",
    )

    npda_user = ForeignKey(
        to="npda.NPDAUser",
        on_delete=CASCADE,
        related_name="paediatric_diabetes_units",
    )
