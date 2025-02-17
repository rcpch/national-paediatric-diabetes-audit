"""Tests relating to behaviour of transfers.

Generally, create a Patient in PDU1, then transfer to PDU2 -> assert the KPIs for both PDUs.
"""

from datetime import date
import logging
from typing import List

import pytest
from dateutil.relativedelta import relativedelta

from project.constants.diabetes_types import DIABETES_TYPES
from project.constants.leave_pdu_reasons import LEAVE_PDU_REASONS
from project.npda.kpi_class.kpis import CalculateKPIS, KPIResult
from project.npda.models import Patient
from project.npda.models.transfer import Transfer
from project.npda.tests.factories.paediatrics_diabetes_unit_factory import (
    PaediatricsDiabetesUnitFactory,
)
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.transfer_factory import TransferFactory
from project.npda.tests.factories.visit_factory import VisitFactory
from project.npda.tests.kpi_calculations.test_calculate_kpis import (
    assert_kpi_result_equal,
)

# Logging
logger = logging.getLogger(__name__)

# Base PZ code before transfer
ORIGINAL_PZ_CODE = "PZ130"
# New PZ code after transfer
NEW_PZ_CODE = "PZ131"
# Moved out of area
MOVED_OUT_OF_AREA_REASON = LEAVE_PDU_REASONS[1][0]


def transfer_patient(
    current_patient_transfer_instance: Transfer,
    new_pz_code: str,
    date_leaving_service: date,
    reason_leaving_service: int = MOVED_OUT_OF_AREA_REASON,
) -> Transfer:
    """Update the current transfer record with the new PZ code and date leaving service.
    
    Currently, a "transfer" is just updating the current transfer record with previous pz_code
    and date/reason leaving service.
    """

    # First update the current transfer record
    current_patient_transfer_instance.date_leaving_service = date_leaving_service
    current_patient_transfer_instance.reason_leaving_service = reason_leaving_service
    # set previous_pz_code to the current PZ code
    current_patient_transfer_instance.previous_pz_code = (
        current_patient_transfer_instance.paediatric_diabetes_unit.pz_code
    )
    current_patient_transfer_instance.save()

    return current_patient_transfer_instance


@pytest.mark.django_db
def test_transfer_behaviour_for_kpi_calculation_1(AUDIT_START_DATE):
    """Tests the transfer behaviour for KPI1"""

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create  Patients and Visits that should PASS KPI1
    eligible_patient: List[Patient] = PatientFactory.create(
        visit__visit_date=AUDIT_START_DATE + relativedelta(days=1),
        date_of_birth=AUDIT_START_DATE - relativedelta(days=365 * 10),
        postcode="eligible_patients",
    )

    # The default pz_code is "PZ130" for PaediatricsDiabetesUnitFactory
    calc_kpis = CalculateKPIS(
        calculation_date=AUDIT_START_DATE,
        return_pt_querysets=True,
    )

    transfer_record_before_transfer = eligible_patient.paediatric_diabetes_units.filter(
        paediatric_diabetes_unit__pz_code="PZ130"
    )

    assert (
        transfer_record_before_transfer.count() == 1
    ), f"Patient {eligible_patient} does not have a transfer instance in PZ130"

    # Make the transfer at 3months after the audit start date
    transfer_record_after_transfer = transfer_patient(
        current_patient_transfer_instance=transfer_record_before_transfer.first(),
        new_pz_code=NEW_PZ_CODE,
        date_leaving_service=AUDIT_START_DATE + relativedelta(months=3),
    )

    kpi_calc_result_obj_old = calc_kpis.calculate_kpis_for_pdus(
        pz_codes=[
            ORIGINAL_PZ_CODE,
        ],
        kpi_idxs=[1],
    )
    kpi_calc_result_obj_new = calc_kpis.calculate_kpis_for_pdus(
        pz_codes=[
            NEW_PZ_CODE,
        ],
        kpi_idxs=[1],
    )

    breakpoint()
