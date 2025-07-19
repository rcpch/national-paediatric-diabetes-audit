from dateutil.relativedelta import relativedelta
from django.db.models import (
    BooleanField,
    Case,
    Exists,
    F,
    OuterRef,
    When,
)
from django.shortcuts import render
from project.npda.kpi_class.kpis import CalculateKPIS
from project.npda.views.dashboard import helpers as hp
from project.npda.views.decorators import login_and_otp_required
from project.npda.models import Visit, Submission, AuditPeriod


@login_and_otp_required()
def patient_measurements(request):
    pz_code = request.session.get("pz_code")

    audit_period = AuditPeriod.objects.get_audit_period_for_request(request)
    calculation_date = audit_period.kpi_calculation_date()
    
    calculate_kpis = CalculateKPIS(
        calculation_date=calculation_date, return_pt_querysets=True, is_jersey=pz_code == "PZ248"
    )

    kpi_calculations_object = calculate_kpis.calculate_kpis_for_pdus(pz_codes=[pz_code])


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

    current_submission = Submission.objects.get_submission_for_request(request, audit_period=audit_period)

    if current_submission:
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

    returned_patient_health_check_totals = patient_health_check_totals(
        pz_code=pz_code,
        calculation_date=calculation_date,
    )

    context={
        "selected_audit_year": audit_period.audit_year(),
        "pz_code": pz_code,
        "hba1c_value_counts_stratified_by_diabetes_type": hba1c_value_counts_stratified_by_diabetes_type,
        "submission_visit_error_count": submission_visit_error_count,
        "submission_date": submission_date,
        "affected_patients": affected_patients,
        "health_check_totals": returned_patient_health_check_totals,
    }
    context.update(**returned_patient_health_check_totals)
    

    return render(
        request=request,
        context=context,
        template_name=template
    )

def patient_health_check_totals(pz_code, calculation_date):
    """
    Returns the totals for the patient health check KPIs.
    Note this repeats some of the logic in the patient_report. Probably should be refactored into a common function.
    This function calculates the totals for the health checks for all T1DM patients in a given PZ code for a specific calculation date.
    It uses the CalculateKPIS class to get the patient querysets and then applies the necessary filters and annotations to calculate the totals for each health check KPI
    """
    calculate_kpis = CalculateKPIS(
        calculation_date=calculation_date, return_pt_querysets=True, is_jersey=pz_code == "PZ248"
    )
    calculate_kpis.set_patients_for_calculation(pz_codes=[pz_code])
    # Select all T1DM patients for PZ code - Note that Jersey (PZ248) has a different patient identifier field
    patient_identifier = (
            "nhs_number" if pz_code != "PZ248" else "unique_reference_number"
        )
    all_t1dm_pts = (
        calculate_kpis.calculate_kpi_3_total_t1dm()
        .patient_querysets["eligible"]
        .annotate(patient_identifier=F(patient_identifier))
    )
    all_t1dm_pts_with_complete_year_of_care = (
        calculate_kpis.calculate_kpi_5_total_t1dm_complete_year().patient_querysets[
            "eligible"
        ]
    )
    pt_qs = all_t1dm_pts.annotate(
        is_complete_year_of_care=Case(
            When(
                Exists(
                    all_t1dm_pts_with_complete_year_of_care.filter(
                        pk=OuterRef("pk")
                    )
                ),
                then=True,
            ),
            default=False,
            output_field=BooleanField(),
        )
    )

    # Use the patient querysets to calculate totals
    # Pre-calculate totals for the health checks from the base queryset before adding category-specific annotations
    complete_year_patients = pt_qs.filter(is_complete_year_of_care=True)
    
    # Calculate totals using the KPI methods directly
    
    total_passed_bmi = calculate_kpis.calculate_kpi_26_bmi().patient_querysets["passed"].filter(
        pk__in=complete_year_patients.values_list("pk", flat=True)
    ).count()
    total_eligible_bmi = complete_year_patients.count()
    
    total_passed_thyroid_screen = calculate_kpis.calculate_kpi_27_thyroid_screen().patient_querysets["passed"].filter(
        pk__in=complete_year_patients.values_list("pk", flat=True)
    ).count()
    total_eligible_thyroid_screen = complete_year_patients.count()
    
    # For age-specific checks (12+ years old)
    complete_year_12plus = complete_year_patients.filter(
        date_of_birth__lte=calculation_date - relativedelta(years=12)
    )
    
    total_passed_blood_pressure = calculate_kpis.calculate_kpi_28_blood_pressure().patient_querysets["passed"].filter(
        pk__in=complete_year_12plus.values_list("pk", flat=True)
    ).count()
    total_eligible_blood_pressure = complete_year_12plus.count()
    
    total_passed_urinary_albumin = calculate_kpis.calculate_kpi_29_urinary_albumin().patient_querysets["passed"].filter(
        pk__in=complete_year_12plus.values_list("pk", flat=True)
    ).count()
    total_eligible_urinary_albumin = complete_year_12plus.count()
    
    total_passed_foot_exam = calculate_kpis.calculate_kpi_31_foot_examination().patient_querysets["passed"].filter(
        pk__in=complete_year_12plus.values_list("pk", flat=True)
    ).count()
    total_eligible_foot_exam = complete_year_12plus.count()
    
    # Gather totals
    return {
        "total_passed_bmi": total_passed_bmi,
        "total_eligible_bmi": total_eligible_bmi,
        "total_passed_thyroid_screen": total_passed_thyroid_screen,
        "total_eligible_thyroid_screen": total_eligible_thyroid_screen,
        "total_passed_blood_pressure": total_passed_blood_pressure,
        "total_eligible_blood_pressure": total_eligible_blood_pressure,
        "total_passed_urinary_albumin": total_passed_urinary_albumin,
        "total_eligible_urinary_albumin": total_eligible_urinary_albumin,
        "total_passed_foot_exam": total_passed_foot_exam,
        "total_eligible_foot_exam": total_eligible_foot_exam,
    }