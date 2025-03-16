# Python imports
from datetime import date

# Django imports
from django.db.models import F, Case, When, Value, CharField, Count, Q
from django.shortcuts import render

# Third party imports
from dateutil.relativedelta import relativedelta

# Project imports
from project.npda.general_functions.audit_period import audit_period_for_audit_year
from project.npda.models import Submission


def patient_characteristics(request):

    diabetes_types = [
        {
            "key": 0,
            "value": "All",
            "enabled": True,
            "tooltip": "All",
            "selected": True,
        },
        {
            "key": 1,
            "value": "Type 1",
            "enabled": False,
            "tooltip": "Type 1 Diabetes",
            "selected": False,
        },
        {
            "key": 2,
            "value": "Type 2",
            "enabled": False,
            "tooltip": "Type 2 Diabetes",
            "selected": False,
        },
        {
            "key": 3,
            "value": "CFRD",
            "enabled": False,
            "tooltip": "Cystic Fibrosis Related Diabetes",
            "selected": False,
        },
        {
            "key": 4,
            "value": "MODY",
            "enabled": False,
            "tooltip": "MODY (monogenic forms of diabetes)",
            "selected": False,
        },
        {
            "key": 5,
            "value": "Other",
            "enabled": False,
            "tooltip": "Other specified Diabetes Mellitus",
            "selected": False,
        },
        {
            "key": 9,
            "value": "Unknown",
            "enabled": False,
            "tooltip": "Unknown/unspecified",
            "selected": False,
        },
    ]

    if request.method == "POST":
        if "diabetes_type" in request.POST:
            for diabetes_type in diabetes_types:
                diabetes_type["selected"] = diabetes_type["key"] == int(
                    request.POST["diabetes_type"]
                )

    template = (
        "dashboard/components/cards/card_partials/patient_characteristics_partial.html"
    )

    audit_year = request.session.get("selected_audit_year", None)

    audit_start, audit_end = audit_period_for_audit_year(audit_year)
    all_patients_in_this_submission = (
        Submission.objects.filter(
            audit_year__range=(audit_start.year, audit_end.year),
            submission_active=True,
            paediatric_diabetes_unit__pz_code=request.session.get("pz_code"),
        )
        .get()
        .patients.all()
    )

    # Get the number of patients in the submission
    number_of_patients = all_patients_in_this_submission.count()

    # This function might get called on historical cohorts, so we need to check if today's date is within the audit period
    if audit_start <= date.today() <= audit_end:
        comparison_date = date.today()
    else:
        comparison_date = audit_end

    filter = Q()
    if request.POST.get("diabetes_type"):
        if request.POST.get("diabetes_type") != "0":
            filter &= Q(
                diabetes_type=int(request.POST.get("diabetes_type"))
            )  # Filter by diabetes type

    # Get the number of patients of ages 0-2, 2-5, 5-12, 12-16, 16-19, 19-25
    all_patients_in_this_submission_by_age = all_patients_in_this_submission.filter(
        filter
    ).values(
        "pk",
        "sex",
        "date_of_birth",
        "index_of_multiple_deprivation_quintile",
        "diabetes_type",
    )

    # Get the number of patients of ages 0-2, 2-5, 5-12, 12-16, 16-19, 19-25
    age_band_counts = {
        "birth_two": 0,
        "two_five": 0,
        "five_twelve": 0,
        "twelve_sixteen": 0,
        "sixteen_nineteen": 0,
        "nineteen_twenty_five": 0,
        "under_twelve": 0,
        "over_twelve": 0,
    }

    sex_counts = {
        "male": 0,
        "female": 0,
        "not_known": 0,
        "not_specified": 0,
    }

    for patient in all_patients_in_this_submission_by_age:
        patient["age"] = relativedelta(comparison_date, patient["date_of_birth"]).years

        # Enable the diabetes types that exist  in the filter
        for dmtype in diabetes_types:
            if patient["diabetes_type"] == dmtype["key"]:
                dmtype["enabled"] = True

        if 0 <= patient["age"] < 2:
            age_band_counts["birth_two"] += 1
        elif 2 <= patient["age"] < 5:
            age_band_counts["two_five"] += 1
        elif 5 <= patient["age"] < 12:
            age_band_counts["five_twelve"] += 1
        elif 12 <= patient["age"] < 16:
            age_band_counts["twelve_sixteen"] += 1
        elif 16 <= patient["age"] < 19:
            age_band_counts["1sixteen_nineteen"] += 1
        elif 19 <= patient["age"] < 25:
            age_band_counts["nineteen_twenty_five"] += 1

        if patient["age"] < 12:
            age_band_counts["under_twelve"] += 1
        elif patient["age"] >= 12:
            age_band_counts["over_twelve"] += 1

        if patient["sex"] == 1:
            sex_counts["male"] += 1
        elif patient["sex"] == 2:
            sex_counts["female"] += 1
        elif patient["sex"] == 0:
            sex_counts["not_known"] += 1
        elif patient["sex"] == 9:
            sex_counts["not_specified"] += 1

    context = {
        "number_of_patients": number_of_patients,
        "patients_by_age": age_band_counts,
        "patients_by_sex": sex_counts,
        "diabetes_types": diabetes_types,
    }

    return render(request, template, context)
