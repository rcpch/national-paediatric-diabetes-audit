from django.shortcuts import render
from project.npda.general_functions.audit_period import audit_period_for_audit_year
from project.npda.kpi_class.kpis import CalculateKPIS
from project.npda.views.dashboard import helpers as hp
from project.npda.views.decorators import login_and_otp_required
from project.npda.models import Visit, Submission, AuditPeriod


@login_and_otp_required()
def patient_measurements(request):

    # First need to get the relevant calculations
    pz_code = request.session.get("pz_code")

    audit_period = AuditPeriod.objects.get_audit_period_for_request(request)
    calculation_date = audit_period.kpi_calculation_date()
    
    calculate_kpis = CalculateKPIS(
        calculation_date=calculation_date, return_pt_querysets=True
    )

    calculate_kpis.calculate_kpis_for_pdus(pz_codes=[pz_code])

    # {
    #     "all": {
    #         "mean_mmol_mol": 58.1,
    #         "mean_percent": 7.3,
    #         "median_mmol_mol": 54.0,
    #         "median_percent": 6.9,
    #     },
    #     "t1dm": {
    #         "mean_mmol_mol": 58.5,
    #         "mean_percent": 7.4,
    #         "median_mmol_mol": 54.0,
    #         "median_percent": 6.9,
    #     },
    #     "t2dm": {
    #         "mean_mmol_mol": 58.8,
    #         "mean_percent": 7.4,
    #         "median_mmol_mol": 55.0,
    #         "median_percent": 7.0,
    #     },
    #     "other": {
    #         "mean_mmol_mol": 57.8,
    #         "mean_percent": 7.3,
    #         "median_mmol_mol": 53.5,
    #         "median_percent": 6.9,
    #     },
    # }
    hba1c_value_counts_stratified_by_diabetes_type = (
        calculate_kpis.calculate_kpi_hba1c_vals_stratified_by_diabetes_type()
    )

    if Submission.objects.filter(
        audit_year=audit_period.audit_year(),
        paediatric_diabetes_unit__pz_code=pz_code,
        paediatric_diabetes_unit__active=True,
        submission_active=True,
    ).exists():
        current_submission = Submission.objects.filter(
            audit_year=audit_period.audit_year(),
            paediatric_diabetes_unit__pz_code=pz_code,
            paediatric_diabetes_unit__active=True,
            submission_active=True,
        ).get()
        visits = Visit.objects.filter(patient__in=current_submission.patients.all())
        submission_visits_with_errors = visits.filter(errors__isnull=False)
        submission_visit_error_count = submission_visits_with_errors.count()
        submission_date = current_submission.submission_date
        affected_patients = submission_visits_with_errors.values("patient").distinct().count()
    else:
        submission_visit_error_count = 0
        submission_date = None
        affected_patients = 0

    template = (
        "dashboard/components/cards/card_partials/patient_measurements_partial.html"
    )

    return render(
        request,
        template_name=template,
        context={
            "selected_audit_year": audit_period.audit_year(),
            "pz_code": pz_code,
            "hba1c_value_counts_stratified_by_diabetes_type": hba1c_value_counts_stratified_by_diabetes_type,
            "submission_visit_error_count": submission_visit_error_count,
            "submission_date": submission_date,
            "affected_patients": affected_patients,
        },
    )
