from django.contrib.gis.db.models import Model, CharField
from django.utils.translation import gettext_lazy as _


class OrganisationEmployer(Model):
    ods_code = CharField(
        _("Employing organisation"),
        help_text=_("Enter your employing organisation"),
        max_length=150,
        null=True,
        blank=True,
    )
    name = CharField(
        _("Employing organisation name"),
        help_text=_("Enter your employing organisation name"),
        max_length=150,
        null=True,
        blank=True,
    )
    pz_code = CharField(
        _("Paediatric Diabetes Unit code"),
        help_text=_("Enter your employing organisation postcode"),
        max_length=150,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Organisation Employer"
        verbose_name_plural = "Organisation Employers"

    def __str__(self):
        return self.name
