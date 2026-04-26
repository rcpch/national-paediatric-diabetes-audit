# python imports
import json
import logging
import os

# third-party imports
import geopandas as gpd
import pandas as pd
from django.apps import apps

# django imports
from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db.models import Q

logger = logging.getLogger(__name__)

"""
Functions to return scatter plot of children by postcode
"""


def get_children_by_pdu_audit_year(
    submission, paediatric_diabetes_unit_lead_organisation
):
    """
    Returns a list of children by postcode for a given audit year and paediatric diabetes unit
    """
    Patient = apps.get_model("npda", "Patient")

    if submission is None:
        return Patient.objects.none()

    patients = submission.patients.all()

    if patients:
        filtered_patients = patients.filter(
            ~Q(postcode__isnull=True)
            | ~Q(postcode__exact=""),  # Exclude patients with no postcode or location
            ~Q(location_wgs84__isnull=True),
        )

        filtered_patients = filtered_patients.annotate(
            distance_from_lead_organisation=Distance(
                "location_wgs84",
                Point(
                    paediatric_diabetes_unit_lead_organisation["longitude"],
                    paediatric_diabetes_unit_lead_organisation["latitude"],
                    srid=4326,
                ),
            )
        ).values(
            "pk",
            "nhs_number",
            "unique_reference_number",
            "location_bng",
            "location_wgs84",
            "distance_from_lead_organisation",
        )

        return filtered_patients

    else:
        return Patient.objects.none()


def generate_dataframe_and_aggregated_distance_data_from_cases(filtered_cases):
    """
    Returns a dataframe of all Cases, location data and distances with aggregated results.
    Returns a tuple:
    1. Aggregated distances from the lead organisation.
    2. Per-patient dataframe with distance fields.
    """

    def _empty_aggregated_distances():
        return {
            "max_distance_travelled_km": "~",
            "mean_distance_travelled_km": "~",
            "min_distance_travelled_km": "~",
            "median_distance_travelled_km": "~",
            "std_distance_travelled_km": "~",
            "max_distance_travelled_mi": "~",
            "mean_distance_travelled_mi": "~",
            "min_distance_travelled_mi": "~",
            "median_distance_travelled_mi": "~",
            "std_distance_travelled_mi": "~",
        }

    geo_df = pd.DataFrame(filtered_cases)

    if not geo_df.empty:
        if "location_wgs84" in geo_df.columns:
            # Filter out rows with None or invalid geometry before processing
            geo_df = geo_df[geo_df["location_wgs84"].notna()]

            # Additional validation to ensure geometries are valid
            valid_geometries = []
            for idx, row in geo_df.iterrows():
                try:
                    # Test if we can access x and y coordinates
                    if row["location_wgs84"] is not None:
                        _ = row["location_wgs84"].x
                        _ = row["location_wgs84"].y
                        valid_geometries.append(idx)
                except (AttributeError, Exception):  # noqa: S112
                    # Skip rows with invalid geometries
                    continue

            # Keep only rows with valid geometries
            geo_df = geo_df.loc[valid_geometries]

            # Check if we still have data after filtering
            if geo_df.empty:
                return _empty_aggregated_distances(), pd.DataFrame()

            # Now safely extract coordinates
            geo_df["longitude"] = geo_df["location_wgs84"].apply(
                lambda loc: loc.x if loc is not None else None
            )
            geo_df["latitude"] = geo_df["location_wgs84"].apply(
                lambda loc: loc.y if loc is not None else None
            )
            geo_df["distance_km"] = geo_df["distance_from_lead_organisation"].apply(
                lambda d: d.km if d is not None else 0
            )
            geo_df["distance_mi"] = geo_df["distance_from_lead_organisation"].apply(
                lambda d: d.mi if d is not None else 0
            )

            # Remove any rows that still have None values after coordinate extraction
            geo_df = geo_df.dropna(subset=["longitude", "latitude"])

            if geo_df.empty:
                return _empty_aggregated_distances(), pd.DataFrame()

            max_distance_travelled_km = geo_df["distance_km"].max()
            mean_distance_travelled_km = geo_df["distance_km"].mean()
            min_distance_travelled_km = geo_df["distance_km"].min()
            median_distance_travelled_km = geo_df["distance_km"].median()
            std_distance_travelled_km = geo_df["distance_km"].std()

            max_distance_travelled_mi = geo_df["distance_mi"].max()
            mean_distance_travelled_mi = geo_df["distance_mi"].mean()
            min_distance_travelled_mi = geo_df["distance_mi"].min()
            median_distance_travelled_mi = geo_df["distance_mi"].median()
            std_distance_travelled_mi = geo_df["distance_mi"].std()

            return {
                "max_distance_travelled_km": f"{max_distance_travelled_km:.2f}",
                "mean_distance_travelled_km": f"{mean_distance_travelled_km:.2f}",
                "min_distance_travelled_km": f"{min_distance_travelled_km:.2f}",
                "median_distance_travelled_km": f"{median_distance_travelled_km:.2f}",
                "std_distance_travelled_km": f"{std_distance_travelled_km:.2f}",
                "max_distance_travelled_mi": f"{max_distance_travelled_mi:.2f}",
                "mean_distance_travelled_mi": f"{mean_distance_travelled_mi:.2f}",
                "min_distance_travelled_mi": f"{min_distance_travelled_mi:.2f}",
                "median_distance_travelled_mi": f"{median_distance_travelled_mi:.2f}",
                "std_distance_travelled_mi": f"{std_distance_travelled_mi:.2f}",
            }, geo_df

    # Return empty/default values if no valid data
    empty_df = pd.DataFrame(
        {
            "pk": [],
            "longitude": [],
            "latitude": [],
            "distance_km": [],
            "distance_mi": [],
        }
    )

    return _empty_aggregated_distances(), empty_df


def generate_geojson_of_imd_and_lsoa_boundaries_for_country(
    country="england", super_generalised=True
):
    """
    lsoa 2011 boundaries and identifiers - 34753 records (England & Wales): "LSOA_2011_Boundaries_Super_Generalised_Clipped_BSC_EW_V4_8608708935797446279.geojson
    imd England 2019 data - 32844 records (England): "IMD2019.xlsx"
    imd Wales 2019 data - 1909 records (Wales): "Index_of_Multiple_Deprivation_(Dec_2019)_Lookup_in_Wales.geojson

    This generates two files (one for England and one for Wales) that contain the merged LSOA boundaries and IMD data as GeoJSON files
    This is used to generate the choropleth map of IMD data

    This function is only used to generate the files and should not be called in production
    """

    if super_generalised:
        file_path = os.path.join(
            settings.BASE_DIR,
            "project",
            "constants",
            "English IMD 2019",
            "LSOA_2011_Boundaries_Super_Generalised_Clipped_BSC_EW_V4_8608708935797446279.geojson",
        )
    else:
        file_path = os.path.join(
            settings.BASE_DIR,
            "project",
            "constants",
            "English IMD 2019",
            "LSOA_Dec_2011_Boundaries_Generalised_Clipped_BGC_EW_V3_-335161623626682850.geojson",
        )
    england_wales_lsoas = gpd.read_file(file_path)  # 34753 LSOAs

    path = os.path.join(
        settings.BASE_DIR,
        "project",
        "constants",
        "English IMD 2019",
        "IMD2019.xlsx",
    )
    england_imd = pd.read_excel(
        path, sheet_name="IMD2019"
    )  # 32844 LSOAs: IMD data for England 2019 without geometry

    file_path = os.path.join(
        settings.BASE_DIR,
        "project",
        "constants",
        "English IMD 2019",
        "Index_of_Multiple_Deprivation_(Dec_2019)_Lookup_in_Wales.geojson",
    )
    wales_imd = gpd.read_file(
        file_path
    )  # 1909 LSOAs: IMD data for Wales 2019 without geometry

    # Rename columns in wales_gdf to match england_imd
    wales_imd = wales_imd.rename(
        columns={
            "lsoa11cd": "LSOA code (2011)",
            "lsoa11nm": "LSOA name (2011)",
            "lsoa11nmw": "LSOA name (2011) (Welsh)",
            "wimd_2019": "Index of Multiple Deprivation (IMD) Rank",
        }
    )

    # convert Index of Multiple Deprivation (IMD) Rank to to decile with name Index of Multiple Deprivation (IMD) Decile
    wales_imd["Index of Multiple Deprivation (IMD) Decile"] = pd.qcut(
        wales_imd["Index of Multiple Deprivation (IMD) Rank"], 10, labels=False
    )

    england_imd["LSOA code (2011)"] = england_imd["LSOA code (2011)"].astype(str)
    england_wales_lsoas["LSOA11CD"] = england_wales_lsoas["LSOA11CD"].astype(str)
    england_imd["LSOA code (2011)"] = england_imd["LSOA code (2011)"].str.strip()
    england_wales_lsoas["LSOA11CD"] = england_wales_lsoas["LSOA11CD"].str.strip()

    # remove the empty geometry column from Wales
    # wales_imd.drop(columns=["geometry"])

    if country == "england":
        # merge the england&wales imd data with the england&wales geodataframe
        merged_gdf = england_imd.merge(
            england_wales_lsoas[
                ["LSOA11CD", "geometry"]
            ],  # Include only the matching column and geometry
            left_on="LSOA code (2011)",
            right_on="LSOA11CD",
            how="inner",  # Retain only matching rows
        )

        # Convert the result to a GeoDataFrame and set the geometry column
        merged_gdf = gpd.GeoDataFrame(merged_gdf, geometry="geometry")
    else:
        merged_gdf = wales_imd.merge(
            england_wales_lsoas,
            left_on="LSOA code (2011)",
            right_on="LSOA11CD",
            how="inner",  # Use 'inner', 'outer', 'left', or 'right' as needed
        )

    merged_gdf.to_crs(epsg=4326)

    merged_gdf = merged_gdf.__geo_interface__

    generalised = ""
    if super_generalised:
        generalised = "_super_generalised"
    file_name = f"merged_lsoa_{country}{generalised}"

    # # convert the data to geojson
    with open(f"{file_name}.json", "w") as f:
        json.dump(merged_gdf, f)
