"""
TDD: Tests that a patient with the same NHS number (or Unique Reference Number)
cannot be added more than once to the same active submission for the same PDU
via the questionnaire.

The constraint is PDU-scoped:
  - same NHS number in the same PDU's submission → rejected
  - same NHS number in a *different* PDU's submission → allowed
"""

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from project.npda.models import (
    AuditPeriod,
    NPDAUser,
    PaediatricDiabetesUnit,
    Submission,
)
from project.npda.tests.constants_for_tests import ALDER_HEY_PZ_CODE
from project.npda.tests.factories import PatientFactory

NHS_NUMBER = "6239431915"

# A second PDU used in the cross-PDU positive test.
GOSH_PZ_CODE = "PZ196"


def _make_submission(pdu, audit_period, user):
    return Submission.objects.create(
        paediatric_diabetes_unit=pdu,
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=timezone.now(),
        submission_by=user,
        submission_active=True,
    )


@pytest.mark.django_db
def test_duplicate_nhs_number_rejected_within_same_pdu_submission(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
):
    """
    Adding a second patient with the same NHS number to the same PDU's active
    submission must raise ValidationError.  Only the first patient may remain.
    """
    pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
    audit_period = AuditPeriod.objects.get_default_audit_period()
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    submission = _make_submission(pdu, audit_period, user)

    patient1 = PatientFactory(nhs_number=NHS_NUMBER, unique_reference_number=None)
    patient2 = PatientFactory(nhs_number=NHS_NUMBER, unique_reference_number=None)

    # First patient must be accepted.
    submission.add_patient(patient1)
    assert submission.patients.count() == 1

    # Second patient with the same NHS number must be rejected.
    with pytest.raises(ValidationError, match="NHS number"):
        submission.add_patient(patient2)

    # Only the original patient should remain.
    assert submission.patients.count() == 1
    assert submission.patients.filter(pk=patient1.pk).exists()


@pytest.mark.django_db
def test_same_nhs_number_allowed_in_different_pdu_submission(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
):
    """
    The same NHS number may appear in submissions belonging to *different* PDUs
    (e.g. after a patient transfers).  This must not raise.
    """
    ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
    gosh_pdu = PaediatricDiabetesUnit.objects.get(pz_code=GOSH_PZ_CODE)
    audit_period = AuditPeriod.objects.get_default_audit_period()

    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()
    gosh_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE
    ).first()

    ah_submission = _make_submission(ah_pdu, audit_period, ah_user)
    gosh_submission = _make_submission(gosh_pdu, audit_period, gosh_user)

    patient_at_ah = PatientFactory(nhs_number=NHS_NUMBER, unique_reference_number=None)
    patient_at_gosh = PatientFactory(
        nhs_number=NHS_NUMBER, unique_reference_number=None
    )

    ah_submission.add_patient(patient_at_ah)
    # Should NOT raise — different PDU.
    gosh_submission.add_patient(patient_at_gosh)

    assert ah_submission.patients.count() == 1
    assert gosh_submission.patients.count() == 1
