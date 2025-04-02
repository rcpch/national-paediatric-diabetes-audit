"""Tests for the patient report view"""

import logging
from http import HTTPStatus

# Python imports
import pytest

# 3rd party imports
from django.urls import reverse

from project.constants.user import RCPCH_AUDIT_TEAM

# E12 imports
from project.npda.models import NPDAUser
from project.npda.tests.constants_for_tests import ALDER_HEY_PZ_CODE
from project.npda.tests.utils import login_and_verify_user
from project.npda.urls import patient_report_urlpatterns

logger = logging.getLogger(__name__)


def test_anonymous_user_cannot_access_patient_report(
    client,
):
    """Anonymous users should not be able to access the patient report."""

    for url in patient_report_urlpatterns:
        response = client.get(reverse(url.name))
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("login") + "?next=" + reverse(url.name)
