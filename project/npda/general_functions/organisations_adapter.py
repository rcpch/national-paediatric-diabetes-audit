# python imports
from django.apps import apps
from django.db.models import F, Value
from django.db.models.functions import Concat, Coalesce
from .rcpch_nhs_organisations import (
    get_nhs_organisation,
    get_all_nhs_organisations,
    get_all_nhs_organisations_affiliated_with_paediatric_diabetes_unit,
)

from .pdus import (
    get_all_pdus_list_choices,
    get_all_pdus_with_grouped_organisations,
    get_single_pdu_from_pz_code,
    get_single_pdu_from_ods_code,
)

# RCPCH imports
import logging


# Logging
logger = logging.getLogger(__name__)


def organisations_to_populate_select_field(request, user_instance=None):
    """
    This function is used to populate the add_employer field with organisations that the user_instance is NOT already affiliated with, based on request user permissions.
    If no user_instance is provided (as the user form is being created), the function will populate the add_employer field with all organisations that the request user has access to.
    """

    OrganisationEmployer = apps.get_model("npda", "OrganisationEmployer")

    if user_instance:
        if (
            request.user.is_superuser
            or request.user.is_rcpch_audit_team_member
            or request.user.is_rcpch_staff
        ):
            # populate the add_employer field with organisations that the user is not already affiliated with
            organisation_choices = (
                (item[0], item[1])
                for item in get_all_nhs_organisations_affiliated_with_paediatric_diabetes_unit()
                if item[0]
                not in OrganisationEmployer.objects.filter(
                    npda_user=user_instance
                ).values_list(
                    "paediatric_diabetes_unit__organisation_ods_code", flat=True
                )
            )
        else:
            pz_code = request.session.get("pz_code")
            sibling_organisations = get_single_pdu_from_pz_code(
                pz_number=pz_code
            ).organisations

            # filter out organisations that the user is already affiliated with
            organisation_choices = [
                (org.ods_code, org.name)
                for org in sibling_organisations
                if org.ods_code
                not in OrganisationEmployer.objects.filter(
                    npda_user=user_instance
                ).values_list(
                    "paediatric_diabetes_unit__organisation_ods_code", flat=True
                )
            ]
    else:
        # this user is being created - therefore need the organisation_choices to be populated with all organisations based on requesting user permissions
        if (
            request.user.is_superuser
            or request.user.is_rcpch_audit_team_member
            or request.user.is_rcpch_staff
        ):
            # return all organisations that are associated with a paediatric diabetes unit
            organisation_choices = (
                (item[0], item[1])
                for item in get_all_nhs_organisations_affiliated_with_paediatric_diabetes_unit()
            )
        else:
            # return all organisations that are associated with the same paediatric diabetes unit as the request user
            pz_code = request.session.get("pz_code")
            sibling_organisations = get_single_pdu_from_pz_code(
                pz_number=pz_code
            ).organisations

            organisation_choices = [
                (org.ods_code, org.name) for org in sibling_organisations
            ]
    return organisation_choices


def paediatric_diabetes_units_to_populate_select_field(request, user_instance=None):
    """
    This function is used to populate the add_employer field with paediatric diabetes units that the user_instance is NOT already affiliated with, based on request user permissions.
    If no user_instance is provided (as the user form is being created), the function will populate the add_employer field with all paediatric diabetes units that the request user has access to.
    """

    PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")

    if user_instance:
        if (
            request.user.is_superuser
            or request.user.is_rcpch_audit_team_member
            or request.user.is_rcpch_staff
        ):
            # return all paediatric diabetes units excluding those were the user is employed
            return (
                PaediatricDiabetesUnit.objects.all()
                .exclude(npdauser=request.user)
                .order_by("organisation_name")
                .annotate(
                    paediatric_diabetes_unit_name=Coalesce(
                        Concat(F("organisation_name"), Value(" - "), F("parent_name")),
                        F("organisation_name"),
                    )
                )
                .values_list("pz_code", "paediatric_diabetes_unit_name")
            )
        else:
            # return only those paediatric diabetes units that a user is already affiliated with
            PaediatricDiabetesUnit.objects.filter(npdauser=request.user).order_by(
                "organisation_name"
            ).annotate(
                paediatric_diabetes_unit_name=Coalesce(
                    Concat(F("organisation_name"), Value(" - "), F("parent_name")),
                    F("organisation_name"),
                )
            ).values_list(
                "pz_code", "paediatric_diabetes_unit_name"
            )
    else:
        # this user is being created - therefore need the organisation_choices to be populated with all organisations based on requesting user permissions
        if (
            request.user.is_superuser
            or request.user.is_rcpch_audit_team_member
            or request.user.is_rcpch_staff
        ):
            # return all paediatric diabetes units
            return (
                PaediatricDiabetesUnit.objects.all()
                .order_by("organisation_name")
                .annotate(
                    paediatric_diabetes_unit_name=Coalesce(
                        Concat(F("organisation_name"), Value(" - "), F("parent_name")),
                        F("organisation_name"),
                    )
                )
                .values_list("pz_code", "paediatric_diabetes_unit_name")
            )
        else:
            # return all organisations that are associated with the same paediatric diabetes unit as the request user
            PaediatricDiabetesUnit.objects.filter(npdateuser=request.user).order_by(
                "organisation_name"
            ).annotate(
                paediatric_diabetes_unit_name=Coalesce(
                    Concat(F("organisation_name"), Value(" - "), F("parent_name")),
                    F("organisation_name"),
                )
            ).values_list(
                "pz_code", "paediatric_diabetes_unit_name"
            )
