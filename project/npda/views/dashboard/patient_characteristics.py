# Python imports
from datetime import date, timedelta
from decimal import Decimal

# Django imports
from django.db.models import Q, F, Case, When, DecimalField
from django.db.models.functions import Round
from django.shortcuts import render

# Third party imports
from dateutil.relativedelta import relativedelta
import pandas as pd
import plotly.graph_objects as go

# Project imports
from project.npda.general_functions.audit_period import audit_period_for_audit_year
from project.npda.models import Submission
from project.constants.colors import (
    RCPCH_LIGHT_BLUE,
    RCPCH_LIGHT_BLUE_TINT1,
    RCPCH_YELLOW,
    RCPCH_YELLOW_LIGHT_TINT1,
    RCPCH_PINK,
    RCPCH_PINK_LIGHT_TINT1,
    RCPCH_MID_GREY,
    RCPCH_LIGHT_GREY,
    RCPCH_DARK_BLUE,
    RCPCH_LIGHTEST_GREY,
)
from project.constants import HBA1C_FORMATS
from project.npda.models import Visit
from project.npda.views.decorators import login_and_otp_required


@login_and_otp_required()
def patient_ages(request):
    """
    This function is used to generate the patient ages table
    """
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
            "enabled": True,
            "tooltip": "Type 1 Diabetes",
            "selected": False,
        },
        {
            "key": 2,
            "value": "Type 2",
            "enabled": True,
            "tooltip": "Type 2 Diabetes",
            "selected": False,
        },
        {
            "key": 3,
            "value": "CFRD",
            "enabled": True,
            "tooltip": "Cystic Fibrosis Related Diabetes",
            "selected": False,
        },
        {
            "key": 4,
            "value": "MODY",
            "enabled": True,
            "tooltip": "MODY (monogenic forms of diabetes)",
            "selected": False,
        },
        {
            "key": 5,
            "value": "Other",
            "enabled": True,
            "tooltip": "Other specified Diabetes Mellitus",
            "selected": False,
        },
        {
            "key": 9,
            "value": "Unknown",
            "enabled": True,
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

    template = "dashboard/components/cards/card_partials/patient_ages_partial.html"

    audit_year = request.session.get("selected_audit_year", None)

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

    audit_start, audit_end = audit_period_for_audit_year(audit_year)

    number_of_patients = 0

    if Submission.objects.filter(
        audit_year__range=(audit_start.year, audit_end.year),
        submission_active=True,
        paediatric_diabetes_unit__pz_code=request.session.get("pz_code"),
    ).exists():
        all_patients_in_this_submission = (
            Submission.objects.filter(
                audit_year__range=(audit_start.year, audit_end.year),
                submission_active=True,
                paediatric_diabetes_unit__pz_code=request.session.get("pz_code"),
            )
            .get()
            .patients.all()
        )

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

        # Disable the diabetes types that do not exist  in the queryset prior to filtering
        all_patients_in_this_submission.values(
            "diabetes_type",
        )
        for dmtype in diabetes_types:
            if dmtype["key"] != "All" and dmtype[
                "key"
            ] not in all_patients_in_this_submission.values_list(
                "diabetes_type", flat=True
            ):
                dmtype["enabled"] = False
            else:
                dmtype["enabled"] = True

        # Get the number of patients of ages 0-2, 2-5, 5-12, 12-16, 16-19, 19-25
        # Filter these patients by the diabetes type selected or All
        all_patients_in_this_submission_by_age = all_patients_in_this_submission.filter(
            filter
        ).values(
            "pk",
            "sex",
            "date_of_birth",
            "ethnicity",
            "index_of_multiple_deprivation_quintile",
            "diabetes_type",
        )

        number_of_patients = all_patients_in_this_submission_by_age.count()

        for patient in all_patients_in_this_submission_by_age:
            patient["age"] = relativedelta(
                comparison_date, patient["date_of_birth"]
            ).years

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
                age_band_counts["sixteen_nineteen"] += 1
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

    context = {
        "audit_year": (audit_start, audit_end),
        "number_of_patients": number_of_patients,
        "patients_by_age": age_band_counts,
        "diabetes_types": diabetes_types,
        "patients_by_sex": sex_counts,
    }

    return render(request, template, context)


@login_and_otp_required()
def all_patient_charts(request):
    """
    This function is used to generate all the patient characteristics charts
    """
    audit_year = request.session.get("selected_audit_year", None)

    audit_start, audit_end = audit_period_for_audit_year(audit_year)

    imd_counts = {
        "1 (most deprived)": 0,
        "2": 0,
        "3": 0,
        "4": 0,
        "5 (least deprived)": 0,
    }

    ethnicity_counts = {
        "White": 0,
        "Mixed": 0,
        "Asian": 0,
        "Black": 0,
        "Other/Not Stated/Unknown": 0,
    }

    if Submission.objects.filter(
        audit_year__range=(audit_start.year, audit_end.year),
        submission_active=True,
        paediatric_diabetes_unit__pz_code=request.session.get("pz_code"),
    ).exists():
        all_patients_in_this_submission = (
            Submission.objects.filter(
                audit_year__range=(audit_start.year, audit_end.year),
                submission_active=True,
                paediatric_diabetes_unit__pz_code=request.session.get("pz_code"),
            )
            .get()
            .patients.all()
        )

        for patient in all_patients_in_this_submission.values(
            "pk",
            "sex",
            "ethnicity",
            "index_of_multiple_deprivation_quintile",
            "diabetes_type",
        ):

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

            # Ethnicity
            if patient["ethnicity"] in ["A", "B", "C"]:
                ethnicity_counts["White"] += 1
            if patient["ethnicity"] in ["D", "E", "F", "G"]:
                ethnicity_counts["Mixed"] += 1
            if patient["ethnicity"] in ["H", "J", "K", "L", "R"]:
                ethnicity_counts["Asian"] += 1
            if patient["ethnicity"] in ["M", "N", "P"]:
                ethnicity_counts["Black"] += 1
            if patient["ethnicity"] in ["S", "Z", "99"]:
                ethnicity_counts["Other/Not Stated/Unknown"] += 1
    else:
        all_patients_in_this_submission = None

    # Create the IMD pie chart
    imd_piechart = create_piechart(imd_counts, "index_of_multiple_deprivation_quintile")

    # Create the Ethnicity pie chart
    ethnicity_piechart = create_piechart(ethnicity_counts, "ethnicity")

    if all_patients_in_this_submission is None:
        visits = None
    else:
        visits = return_eligible_visits(all_patients_in_this_submission, audit_year)
        # Create a Pandas DataFrame
    df = pd.DataFrame(visits)

    # Create the box plot for sex
    sex_hba1c_mmol_mol_box_plot = create_box_plot(df, "sex") if not df.empty else None
    # Create the box plot for IMD
    imd_hba1c_mmol_mol_box_plot = None
    if not df.empty:
        # We may not have IMD for all patients (invalid postcodes, ZZ99 etc)
        df_all_with_imd = df.dropna(
            subset=["patient__index_of_multiple_deprivation_quintile"]
        )
        imd_hba1c_mmol_mol_box_plot = create_box_plot(
            df_all_with_imd,
            "index_of_multiple_deprivation_quintile",
        )
    # Create the box plot for diabetes types
    diabetes_type_hba1c_mmol_mol_box_plot = (
        create_box_plot(
            df,
            "diabetes_type",
        )
        if not df.empty
        else None
    )

    template = (
        "dashboard/components/cards/card_partials/all_patient_charts_partial.html"
    )

    context = {
        "imd_has_data": not counts_are_zero(imd_counts),
        "ethnicity_has_data": not counts_are_zero(ethnicity_counts),
        "imd_piechart": imd_piechart.to_html(full_html=False) if imd_piechart else None,
        "ethnicity_piechart": (
            ethnicity_piechart.to_html(full_html=False) if imd_piechart else None
        ),
        "sex_box_plot": (
            sex_hba1c_mmol_mol_box_plot.to_html(full_html=False)
            if sex_hba1c_mmol_mol_box_plot
            else None
        ),
        "imd_box_plot": (
            imd_hba1c_mmol_mol_box_plot.to_html(full_html=False)
            if imd_hba1c_mmol_mol_box_plot
            else None
        ),
        "diabetes_type_box_plot": (
            diabetes_type_hba1c_mmol_mol_box_plot.to_html(full_html=False)
            if diabetes_type_hba1c_mmol_mol_box_plot
            else None
        ),
        "audit_year": (audit_start, audit_end),
    }

    return render(request, template, context)


"""
# Helper functions for the two views
"""


def _build_pie_chart(field):
    """
    # Build the pie chart for the patient characteristics
    """
    if field == "index_of_multiple_deprivation_quintile":
        colors = [
            "#E00087",  # IMD 1
            "#D3D3D3",  # Light Gray (IMD 2)
            "#A9A9A9",  # Dark Gray (IMD 3)
            "#808080",  # Gray (IMD 4)
            "#11A7F2",  # IMD 5
        ]
        title = "<b>Index of Multiple Deprivation (IMD) Distribution</b>"
        legend_order = ["1 (most deprived)", "2", "3", "4", "5 (least deprived)"]
        legend_title = "IMD Quintiles"
    elif field == "ethnicity":
        colors = [
            RCPCH_LIGHT_BLUE,  # White
            RCPCH_YELLOW,  # Mixed
            RCPCH_PINK,  # Asian
            RCPCH_MID_GREY,  # Black
            RCPCH_DARK_BLUE,  # Other
        ]
        title = "<b>Ethnicity Distribution</b>"
        legend_order = ["White", "Mixed", "Asian", "Black", "Other/Not Stated/Unknown"]
        legend_title = "Ethnicity"

    return colors, title, legend_order, legend_title


def create_piechart(dict_counts, field):
    """
    Generates a Plotly pie chart from IMD counts.

    Args:
        imd_counts (dict): A dictionary where keys are IMD levels (1-5) and values are counts.

    Returns:
        plotly.graph_objects.Figure: A Plotly pie chart figure.
    """

    colors, title, legend_order, legend_title = _build_pie_chart(field)

    labels = list(dict_counts.keys())
    values = list(dict_counts.values())

    # Sort the labels and values in the order of the legend
    ordered_labels = []
    ordered_values = []
    for cat in legend_order:
        if cat in labels:
            ordered_labels.append(cat)
            ordered_values.append(dict_counts[cat])
    labels = ordered_labels
    values = ordered_values

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors,
                textposition="inside",
                showlegend=True,
                hole=0.4,  # Donut chart
                hovertemplate="IMD quintile: %{label}<br>Number of children: %{value}<br>Percentage: %{percent}<extra></extra>",
                sort=False,
            )
        ]
    )

    fig.update_layout(
        title={
            "text": title,
            "font": {
                "size": 14,
                "color": "#0D0D58",  # RCPCH dark blue
                "family": "Montserrat",
            },
        },
        margin=dict(l=20, r=20, t=50, b=20),  # minimal margins
        height=500,
        width=600,
    )

    return fig


def counts_are_zero(counts):
    return all(count == 0 for count in counts.values())


def return_eligible_visits(patients, audit_year):

    visit_value_cols = {
        "patient__pk",
        "hba1c_mmol_mol",
        "hba1c_percent",
        "patient__nhs_number",
        "patient__sex",
        "patient__diabetes_type",
        "patient__index_of_multiple_deprivation_quintile",
    }

    audit_start, audit_end = audit_period_for_audit_year(audit_year)
    return (
        Visit.objects.filter(
            visit_date__range=(audit_start, audit_end),
            hba1c_date__gt=F("patient__diagnosis_date") + timedelta(days=90),
            patient__in=patients,
            hba1c__isnull=False,
        )
        .annotate(
            hba1c_mmol_mol=Case(
                When(
                    hba1c_format=HBA1C_FORMATS[0][0],
                    then=F("hba1c"),
                ),
                When(
                    hba1c_format=HBA1C_FORMATS[1][0],
                    then=F("hba1c")
                    - Round(
                        Decimal("2.152") / Decimal("0.09148")
                    ),  # HbA1c (mmol/mol) = (HbA1c (%) - 2.152) / 0.09148
                ),
                default=F("hba1c"),
                output_field=DecimalField(max_digits=5, decimal_places=2, null=True),
            ),
            hba1c_percent=Case(
                When(
                    hba1c_format=HBA1C_FORMATS[1][0],
                    then=F("hba1c"),
                ),
                When(
                    hba1c_format=HBA1C_FORMATS[0][0],
                    then=F("hba1c") * Decimal("0.09148")
                    + Round(Decimal("2.152")),  # 0.09148 * HbA1c (mmol/mol)) + 2.152
                ),
            ),
        )
        .values(*visit_value_cols)
    )


def _build_box_plot(
    df, field, line_colors, fill_colors, title, xaxis_title, category_order=None
):
    """
    Create the box plot using Plotly Graph Objects
    Shows all categories in category_order, even if they have no data
    """
    fig = go.Figure()

    # If DataFrame is empty or None, still create the plot with empty boxes
    if df is None or df.empty:
        for item in category_order:
            fig.add_trace(
                go.Box(
                    y=[None],  # Empty data
                    name=item,
                    marker_color="rgba(200, 200, 200, 0.5)",  # Light grey
                    fillcolor="rgba(220, 220, 220, 0.5)",  # Lighter grey
                    line=dict(width=1, color="rgba(200, 200, 200, 0.5)"),
                    boxpoints=False,  # Don't show outlier points
                    hoverinfo="name",
                    hovertemplate=f"{item}: No data available<extra></extra>",
                )
            )
    else:
        # Round the percentage to 1 decimal place
        df["hba1c_percent"] = df["hba1c_percent"].apply(
            lambda x: round(x, 1) if pd.notnull(x) else x
        )

        # For each category in the specified order, add a trace
        for item in category_order:
            # Find rows where patient field equals the current category
            subset = (
                df[df[f"patient__{field}"] == item] if not df.empty else pd.DataFrame()
            )

            if len(subset) > 0:
                # Category has data - add normal box plot
                fig.add_trace(
                    go.Box(
                        y=subset["hba1c_mmol_mol"],
                        name=item,
                        marker_color=line_colors[item],
                        fillcolor=fill_colors[item],
                    )
                )

                custom_data = subset.to_dict("records")

                # Add scatter plot on top for individual points
                fig.add_trace(
                    go.Scatter(
                        x=[item] * len(subset),  # Position scatter points over the box
                        y=subset["hba1c_mmol_mol"],
                        mode="markers",
                        marker=dict(color="black", size=3, opacity=0.6),
                        name=f"{item} mmol/mol",
                        showlegend=False,  # Don't duplicate legend entries
                        customdata=custom_data,
                        hovertemplate="HbA1c: %{y}<extra></extra> mmol/mol (%{customdata.hba1c_percent} %) for patient %{customdata.patient__pk} (NHS: %{customdata.patient__nhs_number})",
                    )
                )
            else:
                # Category has no data - add "empty" box plot
                fig.add_trace(
                    go.Box(
                        y=[None],  # Empty data
                        name=item,
                        marker_color="rgba(200, 200, 200, 0.5)",  # Light grey
                        fillcolor="rgba(220, 220, 220, 0.5)",  # Lighter grey
                        line=dict(width=1, color="rgba(200, 200, 200, 0.5)"),
                        boxpoints=False,  # Don't show outlier points
                        hoverinfo="name",
                        hovertemplate=f"{item}: No data available<extra></extra>",
                    )
                )

    # Set layout with explicit category ordering
    fig.update_layout(
        title=title,
        yaxis_title="HbA1c (mmol/mol)",
        xaxis_title=xaxis_title,
        xaxis=dict(
            categoryorder="array",
            categoryarray=category_order,
        ),
        legend=dict(traceorder="normal"),
    )

    fig.update_layout(
        title={
            "text": title,
            "font": {
                "size": 14,
                "color": "#0D0D58",  # RCPCH dark blue
                "family": "Montserrat",
            },
        },
        margin=dict(l=20, r=20, t=50, b=20),  # minimal margins
    )

    return fig


def create_box_plot(df, field):
    """
    # Create the parameters for the box plot
    """
    mapping_object = {}
    if field == "sex":
        mapping_object = {1: "Male", 2: "Female", 0: "Not Known", 9: "Not Specified"}
        line_colors = {
            "Male": RCPCH_LIGHT_BLUE,
            "Female": RCPCH_PINK,
            "Not Known": RCPCH_YELLOW,
            "Not Specified": RCPCH_MID_GREY,
        }
        fill_colors = {
            "Male": RCPCH_LIGHT_BLUE_TINT1,
            "Female": RCPCH_PINK_LIGHT_TINT1,
            "Not Known": RCPCH_YELLOW_LIGHT_TINT1,
            "Not Specified": RCPCH_LIGHT_GREY,
        }
        title = "<b>Distribution of HbA1c (mmol/mol) by Sex</b>"
        xaxis_title = "Sex"
        category_order = ["Male", "Female", "Not Known", "Not Specified"]
    elif field == "index_of_multiple_deprivation_quintile":
        mapping_object = {
            1: "1 (most deprived)",
            2: "2",
            3: "3",
            4: "4",
            5: "5 (least deprived)",
        }
        line_colors = {
            "1 (most deprived)": "#E00087",  # IMD 1
            "2": "#D3D3D3",  # Light Gray (IMD 2)
            "3": "#A9A9A9",  # Dark Gray (IMD 3)
            "4": "#808080",  # Gray (IMD 4)
            "5 (least deprived)": "#11A7F2",  # IMD 5
        }
        fill_colors = {
            "1 (most deprived)": RCPCH_PINK_LIGHT_TINT1,  # IMD 1
            "2": RCPCH_LIGHTEST_GREY,  # Light Gray (IMD 2)
            "3": RCPCH_LIGHT_GREY,  # Dark Gray (IMD 3)
            "4": RCPCH_MID_GREY,  # Gray (IMD 4)
            "5 (least deprived)": RCPCH_LIGHT_BLUE_TINT1,  # IMD 5
        }
        title = "<b>Distribution of HbA1c (mmol/mol) by IMD</b>"
        xaxis_title = "Index of Multiple Deprivation (IMD)"
        category_order = ["1 (most deprived)", "2", "3", "4", "5 (least deprived)"]
    elif field == "diabetes_type":
        mapping_object = {
            1: "Type 1",
            2: "Type 2",
            3: "CFRD",
            4: "MODY",
            5: "Other",
            99: "Unknown",
        }
        xaxis_title = "Diabetes Types"
        line_colors = {
            "Type 1": RCPCH_LIGHT_BLUE,
            "Type 2": RCPCH_PINK,
            "CFRD": RCPCH_YELLOW,
            "MODY": RCPCH_MID_GREY,
            "Other": RCPCH_DARK_BLUE,
            "Unknown": RCPCH_LIGHTEST_GREY,
        }
        fill_colors = {
            "Type 1": RCPCH_LIGHT_BLUE_TINT1,
            "Type 2": RCPCH_PINK_LIGHT_TINT1,
            "CFRD": RCPCH_YELLOW_LIGHT_TINT1,
            "MODY": RCPCH_LIGHT_GREY,
            "Other": RCPCH_DARK_BLUE,
            "Unknown": RCPCH_LIGHTEST_GREY,
        }
        title = "<b>Distribution of HbA1c (mmol/mol) by Diabetes Type</b>"
        category_order = ["Type 1", "Type 2", "CFRD", "MODY", "Other", "Unknown"]

    # Map values using the mapping object
    if not df.empty:
        df = df.copy()
        # For IMD, we need special handling to ensure all categories exist
        if field == "index_of_multiple_deprivation_quintile":
            # Create a DataFrame with a single row for each IMD category
            dummy_rows = []
            for key, value in mapping_object.items():
                if key is not None:  # Skip None for now
                    dummy_rows.append(
                        {
                            f"patient__{field}": value,
                            "hba1c_mmol_mol": float(
                                "nan"
                            ),  # Use NaN for missing values
                            "hba1c_percent": float("nan"),
                        }
                    )

            # Create dummy DataFrame with all categories
            dummy_df = pd.DataFrame(dummy_rows)

            # Map the actual data
            df[f"patient__{field}"] = df[f"patient__{field}"].map(mapping_object)

            # Combine with actual data (only used to ensure all categories present)
            combined_df = pd.concat([df, dummy_df], ignore_index=True)
            df = combined_df
        else:
            df[f"patient__{field}"] = df[f"patient__{field}"].map(mapping_object)

        # Convert Decimal to float for plotting
        df["hba1c_mmol_mol"] = df["hba1c_mmol_mol"].astype(float)
        df["hba1c_percent"] = df["hba1c_percent"].astype(float)

    boxplot = _build_box_plot(
        df,
        field,
        line_colors,
        fill_colors,
        title,
        xaxis_title,
        category_order=category_order,
    )
    return boxplot
