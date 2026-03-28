from http import HTTPStatus
from unittest.mock import patch

import pytest

# Django imports
from django.apps import apps
from django.urls import reverse

# RCPCH imports
from project.npda.models import AuditPeriod, NPDAUser, Submission
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory
from project.npda.tests.utils import login_and_verify_user

GOSH_PZ_CODE = "PZ196"
ALDER_HEY_PZ_CODE = "PZ074"


def create_submission_with_patient(user):
    audit_period = AuditPeriod.objects.get_default_audit_period()

    submission = Submission.objects.create(
        audit_year=audit_period.audit_year(),
        audit_period=audit_period,
        submission_date=f"{audit_period.audit_year()}-04-01T00:00:00Z",
        submission_active=True,
        submission_by=user,
        paediatric_diabetes_unit=user.organisation_employers.first(),
    )
    Transfer = apps.get_model("npda.Transfer")
    patient = PatientFactory()
    # Update the transfer to match the user's PDU
    Transfer.objects.filter(patient=patient).update(
        paediatric_diabetes_unit=user.organisation_employers.first()
    )
    submission.patients.add(patient)

    return patient


@pytest.mark.django_db
@patch(
    "project.npda.views.patient.fetch_organisation_by_ods_code",
    return_value={"longitude": -2.9, "latitude": 53.4},
)
def test_users_only_see_patients_from_their_pdu_using_session_url(
    mock_fetch_org,
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """Except for RCPCH_AUDIT_TEAM, users should only see patients from their own PDU."""

    gosh_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE
    ).first()

    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    gosh_patient = create_submission_with_patient(gosh_user)
    ah_patient = create_submission_with_patient(ah_user)

    client = login_and_verify_user(client, ah_user)
    response = client.get(
        reverse(
            "pdu-patients",
            kwargs={
                "audit_period": AuditPeriod.objects.get_default_audit_period().slug,
                "pz_code": ALDER_HEY_PZ_CODE,
            },
        )
    )

    assert response.status_code == HTTPStatus.OK

    patients = response.context_data["object_list"]

    assert len(patients) == 1
    assert patients.first().pk == ah_patient.pk


@pytest.mark.django_db
@patch(
    "project.npda.views.patient.fetch_organisation_by_ods_code",
    return_value={"longitude": -2.9, "latitude": 53.4},
)
def test_users_only_see_patients_from_their_pdu_using_data_url(
    mock_fetch_org,
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """Except for RCPCH_AUDIT_TEAM, users should only see patients from their own PDU."""

    gosh_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE
    ).first()

    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    gosh_patient = create_submission_with_patient(gosh_user)
    ah_patient = create_submission_with_patient(ah_user)

    client = login_and_verify_user(client, ah_user)
    audit_period = AuditPeriod.objects.get_default_audit_period()
    url = reverse(
        "pdu-patients",
        kwargs={"audit_period": audit_period.slug, "pz_code": ALDER_HEY_PZ_CODE},
    )

    response = client.get(url)

    assert response.status_code == HTTPStatus.OK

    patients = response.context_data["object_list"]

    assert len(patients) == 1
    assert patients.first().pk == ah_patient.pk


@pytest.mark.django_db
def test_users_cannot_see_patients_from_other_pdu_using_data_url(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """Except for RCPCH_AUDIT_TEAM, users should only see patients from their own PDU."""

    gosh_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE
    ).first()

    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    gosh_patient = create_submission_with_patient(gosh_user)
    ah_patient = create_submission_with_patient(ah_user)

    client = login_and_verify_user(client, ah_user)
    audit_period = AuditPeriod.objects.get_default_audit_period()
    url = reverse(
        "pdu-patients",
        kwargs={"audit_period": audit_period.slug, "pz_code": GOSH_PZ_CODE},
    )

    response = client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert "context_data" not in response


@pytest.mark.django_db
def test_users_can_only_edit_patients_from_their_own_pdu(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    gosh_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE
    ).first()

    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    ah_patient = create_submission_with_patient(ah_user)

    client = login_and_verify_user(client, gosh_user)

    audit_period = AuditPeriod.objects.get_default_audit_period()
    url = reverse(
        "pdu-patient-update",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
            "pk": ah_patient.pk,
        },
    )
    response = client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
def test_rcpch_audit_team_can_edit_patients_from_any_pdu(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    gosh_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE
    ).first()

    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    rcpch_user = NPDAUser.objects.filter(is_rcpch_audit_team_member=True).first()

    gosh_patient = create_submission_with_patient(gosh_user)
    ah_patient = create_submission_with_patient(ah_user)

    client = login_and_verify_user(client, rcpch_user)

    audit_period = AuditPeriod.objects.get_default_audit_period()

    gosh_url = reverse(
        "pdu-patient-update",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": GOSH_PZ_CODE,
            "pk": gosh_patient.pk,
        },
    )
    assert client.get(gosh_url).status_code == HTTPStatus.OK

    ah_url = reverse(
        "pdu-patient-update",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
            "pk": ah_patient.pk,
        },
    )
    assert client.get(ah_url).status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_users_can_only_see_patient_visits_from_their_own_pdu(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    gosh_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE
    ).first()

    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    ah_patient = create_submission_with_patient(ah_user)

    client = login_and_verify_user(client, gosh_user)

    audit_period = AuditPeriod.objects.get_default_audit_period()
    url = reverse(
        "pdu-patient-visits",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
            "patient_id": ah_patient.pk,
        },
    )

    response = client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
def test_rcpch_audit_team_can_see_visits_from_all_pdus(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    gosh_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE
    ).first()

    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    rcpch_user = NPDAUser.objects.filter(is_rcpch_audit_team_member=True).first()

    gosh_patient = create_submission_with_patient(gosh_user)
    ah_patient = create_submission_with_patient(ah_user)

    client = login_and_verify_user(client, rcpch_user)

    audit_period = AuditPeriod.objects.get_default_audit_period()
    gosh_url = reverse(
        "pdu-patient-visits",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": GOSH_PZ_CODE,
            "patient_id": gosh_patient.pk,
        },
    )

    assert client.get(gosh_url).status_code == HTTPStatus.OK

    ah_url = reverse(
        "pdu-patient-visits",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
            "patient_id": ah_patient.pk,
        },
    )
    assert client.get(ah_url).status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_users_can_only_edit_patient_visits_from_their_own_pdu(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    gosh_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE
    ).first()

    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    ah_patient = create_submission_with_patient(ah_user)
    ah_visit = VisitFactory(patient=ah_patient)

    client = login_and_verify_user(client, gosh_user)

    audit_period = AuditPeriod.objects.get_default_audit_period()

    url = reverse(
        "pdu-visit-update",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": GOSH_PZ_CODE,
            "patient_id": ah_patient.pk,
            "pk": ah_visit.pk,
        },
    )
    response = client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
def test_rcpch_audit_team_can_edit_visits_from_all_pdus(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    gosh_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE
    ).first()

    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    rcpch_user = NPDAUser.objects.filter(is_rcpch_audit_team_member=True).first()

    gosh_patient = create_submission_with_patient(gosh_user)
    gosh_visit = VisitFactory(patient=gosh_patient)

    ah_patient = create_submission_with_patient(ah_user)
    ah_visit = VisitFactory(patient=ah_patient)

    client = login_and_verify_user(client, rcpch_user)

    audit_period = AuditPeriod.objects.get_default_audit_period()

    gosh_url = reverse(
        "pdu-visit-update",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": GOSH_PZ_CODE,
            "patient_id": gosh_patient.pk,
            "pk": gosh_visit.pk,
        },
    )
    assert client.get(gosh_url).status_code == HTTPStatus.OK

    ah_url = reverse(
        "pdu-visit-update",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
            "patient_id": ah_patient.pk,
            "pk": ah_visit.pk,
        },
    )
    assert client.get(ah_url).status_code == HTTPStatus.OK
