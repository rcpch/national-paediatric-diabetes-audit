# Python imports
from datetime import date

# Django imports
from django.db.models import Q
from django.shortcuts import render

# Third party imports
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go

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

    imd_counts = {
        "1 (most deprived)": 0,
        "2": 0,
        "3": 0,
        "4": 0,
        "5 (least deprived)": 0,
    }

    for patient in all_patients_in_this_submission_by_age:
        patient["age"] = relativedelta(comparison_date, patient["date_of_birth"]).years

        # Enable the diabetes types that exist  in the filter
        for dmtype in diabetes_types:
            if patient["diabetes_type"] == dmtype["key"]:
                dmtype["enabled"] = True

        # Count the number of patients in each age band
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

        # count the number of <12 and >12
        if patient["age"] < 12:
            age_band_counts["under_twelve"] += 1
        elif patient["age"] >= 12:
            age_band_counts["over_twelve"] += 1

        # Count the patients by sex
        if patient["sex"] == 1:
            sex_counts["male"] += 1
        elif patient["sex"] == 2:
            sex_counts["female"] += 1
        elif patient["sex"] == 0:
            sex_counts["not_known"] += 1
        elif patient["sex"] == 9:
            sex_counts["not_specified"] += 1

        # Count the patients by IMD
        if patient["index_of_multiple_deprivation_quintile"] == 1:
            imd_counts["1 (most deprived)"] += 1
        elif patient["index_of_multiple_deprivation_quintile"] == 2:
            imd_counts["2"] += 1
        elif patient["index_of_multiple_deprivation_quintile"] == 3:
            imd_counts["3"] += 1
        elif patient["index_of_multiple_deprivation_quintile"] == 4:
            imd_counts["4"] += 1
        elif patient["index_of_multiple_deprivation_quintile"] == 5:
            imd_counts["5 (least deprived)"] += 1

    # Create the IMD pie chart
    imd_piechart = create_imd_piechart(imd_counts)

    context = {
        "number_of_patients": number_of_patients,
        "patients_by_age": age_band_counts,
        "patients_by_sex": sex_counts,
        "patients_by_imd": imd_counts,
        "diabetes_types": diabetes_types,
        "imd_piechart": imd_piechart.to_html(full_html=False),
    }

    return render(request, template, context)


def create_imd_piechart(imd_counts):
    """
    Generates a Plotly pie chart from IMD counts.

    Args:
        imd_counts (dict): A dictionary where keys are IMD levels (1-5) and values are counts.

    Returns:
        plotly.graph_objects.Figure: A Plotly pie chart figure.
    """

    colors = [
        "#E00087",  # IMD 1
        "#D3D3D3",  # Light Gray (IMD 2)
        "#A9A9A9",  # Dark Gray (IMD 3)
        "#808080",  # Gray (IMD 4)
        "#11A7F2",  # IMD 5
    ]

    labels = list(imd_counts.keys())
    values = list(imd_counts.values())

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors,
                texttemplate="%{label}: %{value}",  # Add labels to the slices
                textposition="inside",
                showlegend=True,
                hole=0.4,  # Donut chart
            )
        ]
    )

    fig.update_layout(
        title={
            "text": "<b>Index of Multiple Deprivation (IMD) Distribution</b>",
            "font": {
                "size": 14,
                "color": "#0D0D58",  # RCPCH dark blue
                "family": "Montserrat",
            },
        },
        margin=dict(l=20, r=20, t=50, b=20),  # minimal margins
    )

    return fig
