from django.shortcuts import render

from project.npda.general_functions.patient_report.queries import (
    dashboard_health_check_totals,
    hba1c_stats_by_diabetes_type,
)
from project.npda.models import Submission, Visit
from project.npda.views.decorators import check_data_permissions, login_and_otp_required


@login_and_otp_required()
@check_data_permissions()
def patient_measurements(request, audit_period, pdu):
    pz_code = pdu.pz_code

    hba1c_value_counts_stratified_by_diabetes_type = hba1c_stats_by_diabetes_type(
        pdu, audit_period
    )

    current_submission = Submission.objects.get_submission_for_request(
        pdu, audit_period
    )

    if current_submission:
        visits = Visit.objects.filter(patient__in=current_submission.patients.all())
        submission_visits_with_errors = visits.filter(errors__isnull=False)
        submission_visit_error_count = submission_visits_with_errors.count()
        submission_date = current_submission.submission_date
        affected_patients = (
            submission_visits_with_errors.values("patient").distinct().count()
        )
    else:
        submission_visit_error_count = 0
        submission_date = None
        affected_patients = 0

    template = (
        "dashboard/components/cards/card_partials/patient_measurements_partial.html"
    )

    returned_patient_health_check_totals = dashboard_health_check_totals(
        pdu, audit_period
    )

    context = {
        "pz_code": pz_code,
        "hba1c_value_counts_stratified_by_diabetes_type": hba1c_value_counts_stratified_by_diabetes_type,
        "submission_visit_error_count": submission_visit_error_count,
        "submission_date": submission_date,
        "affected_patients": affected_patients,
        "health_check_totals": returned_patient_health_check_totals,
    }
    context.update(**returned_patient_health_check_totals)

    return render(request=request, context=context, template_name=template)
