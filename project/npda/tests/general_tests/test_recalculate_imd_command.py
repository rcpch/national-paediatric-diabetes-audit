from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from django.core.management import call_command

from project.constants import AUDIT_CENTRE_EDITOR
from project.npda.general_functions.validate_postcode import ValidatedPostcode
from project.npda.models import AuditPeriod, Submission
from project.npda.tests.factories.npda_user_factory import NPDAUserFactory
from project.npda.tests.factories.paediatrics_diabetes_unit_factory import (
    PaediatricsDiabetesUnitFactory,
)
from project.npda.tests.factories.patient_factory import PatientFactory


@pytest.mark.django_db
def test_recalculate_imd_uses_country_and_audit_period_year_mapping():
    audit_period = AuditPeriod.objects.create(
        is_open=False,
        is_visible=True,
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        slug="2026-2027-imd-test",
    )

    pdu = PaediatricsDiabetesUnitFactory(pz_code="PZ401")
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_EDITOR,
        organisation_employers=[pdu.pz_code],
    )

    submission = Submission.objects.create(
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_active=True,
        submission_by=user,
        paediatric_diabetes_unit=pdu,
    )

    england_patient = PatientFactory(
        postcode="SW1A 1AA",
        index_of_multiple_deprivation_quintile=None,
    )
    wales_patient = PatientFactory(
        postcode="CF10 3NQ",
        index_of_multiple_deprivation_quintile=None,
    )
    submission.patients.add(england_patient, wales_patient)

    async def lookup_side_effect(postcode, _async_client):
        if postcode == "SW1A 1AA":
            return ValidatedPostcode(
                normalised_postcode="SW1A 1AA",
                lon=-0.141588,
                lat=51.501009,
                country="England",
            )
        if postcode == "CF10 3NQ":
            return ValidatedPostcode(
                normalised_postcode="CF10 3NQ",
                lon=-3.17909,
                lat=51.481583,
                country="Wales",
            )
        return None

    with (
        patch(
            "project.npda.management.commands.recalculate_imd.lookup_postcode",
            AsyncMock(side_effect=lookup_side_effect),
        ),
        patch(
            "project.npda.management.commands.recalculate_imd.lookup_terminated_postcode",
            AsyncMock(return_value=None),
        ),
        patch(
            "project.npda.management.commands.recalculate_imd.imd_for_postcode",
            AsyncMock(side_effect=[2, 3]),
        ) as mock_imd_for_postcode,
    ):
        call_command("recalculate_imd", "--audit-period", audit_period.slug)

    england_patient.refresh_from_db()
    wales_patient.refresh_from_db()

    assert england_patient.index_of_multiple_deprivation_quintile == 2
    assert wales_patient.index_of_multiple_deprivation_quintile == 3

    calls = [
        (call.args[0], call.kwargs) for call in mock_imd_for_postcode.await_args_list
    ]
    assert ("SW1A 1AA", {"year": 2025, "country": "england"}) in calls
    assert ("CF10 3NQ", {"year": None, "country": "wales"}) in calls


@pytest.mark.django_db
def test_recalculate_imd_dry_run_does_not_persist_changes():
    audit_period = AuditPeriod.objects.create(
        is_open=False,
        is_visible=True,
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        slug="2026-2027-imd-dry-run",
    )

    pdu = PaediatricsDiabetesUnitFactory(pz_code="PZ402")
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_EDITOR,
        organisation_employers=[pdu.pz_code],
    )

    submission = Submission.objects.create(
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_active=True,
        submission_by=user,
        paediatric_diabetes_unit=pdu,
    )

    patient = PatientFactory(
        postcode="SW1A 1AA",
        index_of_multiple_deprivation_quintile=None,
    )
    submission.patients.add(patient)

    with (
        patch(
            "project.npda.management.commands.recalculate_imd.lookup_postcode",
            AsyncMock(
                return_value=ValidatedPostcode(
                    normalised_postcode="SW1A 1AA",
                    lon=-0.141588,
                    lat=51.501009,
                    country="England",
                )
            ),
        ),
        patch(
            "project.npda.management.commands.recalculate_imd.lookup_terminated_postcode",
            AsyncMock(return_value=None),
        ),
        patch(
            "project.npda.management.commands.recalculate_imd.imd_for_postcode",
            AsyncMock(return_value=4),
        ) as mock_imd_for_postcode,
    ):
        call_command(
            "recalculate_imd", "--audit-period", audit_period.slug, "--dry-run"
        )

    patient.refresh_from_db()
    assert patient.index_of_multiple_deprivation_quintile is None
    mock_imd_for_postcode.assert_awaited_once()


@pytest.mark.django_db
def test_recalculate_imd_recalculate_missing_filters_to_calculable_non_jersey_missing():
    audit_period = AuditPeriod.objects.create(
        is_open=False,
        is_visible=True,
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        slug="2026-2027-imd-missing-only",
    )

    pdu = PaediatricsDiabetesUnitFactory(pz_code="PZ403")
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_EDITOR,
        organisation_employers=[pdu.pz_code],
    )

    submission = Submission.objects.create(
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_active=True,
        submission_by=user,
        paediatric_diabetes_unit=pdu,
    )

    missing_valid = PatientFactory(
        postcode="SW1A 1AA",
        index_of_multiple_deprivation_quintile=None,
    )
    existing_imd = PatientFactory(
        postcode="CF10 3NQ",
        index_of_multiple_deprivation_quintile=4,
    )
    missing_unknown_postcode = PatientFactory(
        postcode="ZZ99 3WZ",
        index_of_multiple_deprivation_quintile=None,
    )
    missing_jersey = PatientFactory(
        postcode="JE1 1AA",
        index_of_multiple_deprivation_quintile=None,
    )
    missing_no_postcode = PatientFactory(
        postcode=None,
        index_of_multiple_deprivation_quintile=None,
    )

    submission.patients.add(
        missing_valid,
        existing_imd,
        missing_unknown_postcode,
        missing_jersey,
        missing_no_postcode,
    )

    with (
        patch(
            "project.npda.management.commands.recalculate_imd.lookup_postcode",
            AsyncMock(
                return_value=ValidatedPostcode(
                    normalised_postcode="SW1A 1AA",
                    lon=-0.141588,
                    lat=51.501009,
                    country="England",
                )
            ),
        ) as mock_lookup_postcode,
        patch(
            "project.npda.management.commands.recalculate_imd.lookup_terminated_postcode",
            AsyncMock(return_value=None),
        ) as mock_lookup_terminated_postcode,
        patch(
            "project.npda.management.commands.recalculate_imd.imd_for_postcode",
            AsyncMock(return_value=2),
        ) as mock_imd_for_postcode,
    ):
        call_command(
            "recalculate_imd",
            "--audit-period",
            audit_period.slug,
            "--recalculate-missing",
        )

    missing_valid.refresh_from_db()
    existing_imd.refresh_from_db()
    missing_unknown_postcode.refresh_from_db()
    missing_jersey.refresh_from_db()
    missing_no_postcode.refresh_from_db()

    assert missing_valid.index_of_multiple_deprivation_quintile == 2
    assert existing_imd.index_of_multiple_deprivation_quintile == 4
    assert missing_unknown_postcode.index_of_multiple_deprivation_quintile is None
    assert missing_jersey.index_of_multiple_deprivation_quintile is None
    assert missing_no_postcode.index_of_multiple_deprivation_quintile is None

    mock_lookup_postcode.assert_awaited_once()
    assert mock_lookup_postcode.await_args.args[0] == "SW1A 1AA"
    mock_lookup_terminated_postcode.assert_not_awaited()
    mock_imd_for_postcode.assert_awaited_once()
