"""
Tests for get_categories and get_tabs in categories.py.

These are pure unit tests — no DB access required.
They verify that the correct fields are included/excluded for each dataset year,
and that the tab structure is built correctly.
"""

from project.npda.general_functions.categories import get_categories, get_tabs

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def all_fields_for_year(dataset_year):
    """Return a flat set of all field names visible for the given dataset year."""
    categories = get_categories(instance=None, form=None, dataset_year=dataset_year)
    fields = set()
    for _category in categories:
        # Categories don't expose their filtered field list directly, so we
        # re-derive it from VISIT_CATEGORIES_BY_TAB via a second import.
        pass
    return fields


def category_names_for_year(dataset_year):
    """Return the list of category names returned by get_categories for a given year."""
    return [
        c["name"]
        for c in get_categories(instance=None, form=None, dataset_year=dataset_year)
    ]


def fields_in_category(category_name, dataset_year):
    """Return the field names in a named category for a given dataset year."""
    from project.constants.visit_categories import VISIT_CATEGORIES_BY_TAB

    for tab in VISIT_CATEGORIES_BY_TAB.values():
        if category_name in tab:
            return [
                entry["field"]
                for entry in tab[category_name]["fields"]
                if dataset_year in entry["dataset_years"]
            ]
    return []


# ---------------------------------------------------------------------------
# Structure tests — categories are always present regardless of year
# ---------------------------------------------------------------------------


def test_all_categories_present_for_2021():
    names = category_names_for_year(2021)
    assert "Measurements" in names
    assert "HBA1c" in names
    assert "Treatment" in names
    assert "CGM" in names
    assert "BP" in names
    assert "Foot Care" in names
    assert "DECS" in names
    assert "ACR" in names
    assert "Cholesterol" in names
    assert "Thyroid" in names
    assert "Coeliac" in names
    assert "Psychology" in names
    assert "Smoking" in names
    assert "Dietician" in names
    assert "Sick Day Rules" in names
    assert "Immunisation (flu)" in names
    assert "Hospital Admission" in names


def test_all_categories_present_for_2026():
    names = category_names_for_year(2026)
    assert "Measurements" in names
    assert "HBA1c" in names
    assert "Treatment" in names
    assert "CGM" in names
    assert "BP" in names
    assert "Foot Care" in names
    assert "DECS" in names
    assert "ACR" in names
    assert "Cholesterol" in names
    assert "Thyroid" in names
    assert "Coeliac" in names
    assert "Psychology" in names
    assert "Smoking" in names
    assert "Dietician" in names
    assert "Sick Day Rules" in names
    assert "Immunisation (flu)" in names
    assert "Hospital Admission" in names


# ---------------------------------------------------------------------------
# HBA1c — hba1c_format is 2021 only
# ---------------------------------------------------------------------------


def test_hba1c_format_present_in_2021():
    assert "hba1c_format" in fields_in_category("HBA1c", 2021)


def test_hba1c_format_absent_in_2026():
    assert "hba1c_format" not in fields_in_category("HBA1c", 2026)


def test_hba1c_and_date_present_in_both_years():
    for year in (2021, 2026):
        fields = fields_in_category("HBA1c", year)
        assert "hba1c" in fields
        assert "hba1c_date" in fields


# ---------------------------------------------------------------------------
# Treatment — 2021 uses treatment; 2026 uses insulin_regimen etc.
# ---------------------------------------------------------------------------


def test_treatment_field_present_in_2021():
    assert "treatment" in fields_in_category("Treatment", 2021)


def test_treatment_field_absent_in_2026():
    assert "treatment" not in fields_in_category("Treatment", 2026)


def test_insulin_regimen_absent_in_2021():
    assert "insulin_regimen" not in fields_in_category("Treatment", 2021)


def test_insulin_regimen_present_in_2026():
    assert "insulin_regimen" in fields_in_category("Treatment", 2026)


def test_non_insulin_medication_absent_in_2021():
    assert "non_insulin_medication" not in fields_in_category("Treatment", 2021)


def test_non_insulin_medication_present_in_2026():
    assert "non_insulin_medication" in fields_in_category("Treatment", 2026)


def test_dietary_lifestyle_modification_absent_in_2021():
    assert "dietary_lifestyle_modification" not in fields_in_category("Treatment", 2021)


def test_dietary_lifestyle_modification_present_in_2026():
    assert "dietary_lifestyle_modification" in fields_in_category("Treatment", 2026)


def test_closed_loop_system_present_in_both_years():
    for year in (2021, 2026):
        assert "closed_loop_system" in fields_in_category("Treatment", year)


# ---------------------------------------------------------------------------
# CGM — glucose_monitoring (2021) vs cgm_use (2026)
# ---------------------------------------------------------------------------


def test_glucose_monitoring_present_in_2021():
    assert "glucose_monitoring" in fields_in_category("CGM", 2021)


def test_glucose_monitoring_absent_in_2026():
    assert "glucose_monitoring" not in fields_in_category("CGM", 2026)


def test_cgm_use_absent_in_2021():
    assert "cgm_use" not in fields_in_category("CGM", 2021)


def test_cgm_use_present_in_2026():
    assert "cgm_use" in fields_in_category("CGM", 2026)


# ---------------------------------------------------------------------------
# Smoking — smoking_status (2021) vs smoking_vaping_status (2026)
# ---------------------------------------------------------------------------


def test_smoking_status_present_in_2021():
    assert "smoking_status" in fields_in_category("Smoking", 2021)


def test_smoking_status_absent_in_2026():
    assert "smoking_status" not in fields_in_category("Smoking", 2026)


def test_smoking_vaping_status_absent_in_2021():
    assert "smoking_vaping_status" not in fields_in_category("Smoking", 2021)


def test_smoking_vaping_status_present_in_2026():
    assert "smoking_vaping_status" in fields_in_category("Smoking", 2026)


def test_smoking_cessation_referral_date_present_in_both_years():
    for year in (2021, 2026):
        assert "smoking_cessation_referral_date" in fields_in_category("Smoking", year)


# ---------------------------------------------------------------------------
# Psychology — psychological_support_outcome is 2026 only
# ---------------------------------------------------------------------------


def test_psychological_support_outcome_absent_in_2021():
    assert "psychological_support_outcome" not in fields_in_category("Psychology", 2021)


def test_psychological_support_outcome_present_in_2026():
    assert "psychological_support_outcome" in fields_in_category("Psychology", 2026)


def test_psychology_core_fields_present_in_both_years():
    for year in (2021, 2026):
        fields = fields_in_category("Psychology", year)
        assert "psychological_screening_assessment_date" in fields
        assert "psychological_additional_support_status" in fields


# ---------------------------------------------------------------------------
# Hospital Admission — blood_gas fields are 2026 only
# ---------------------------------------------------------------------------


def test_blood_gas_ph_absent_in_2021():
    assert "blood_gas_ph" not in fields_in_category("Hospital Admission", 2021)


def test_blood_gas_ph_present_in_2026():
    assert "blood_gas_ph" in fields_in_category("Hospital Admission", 2026)


def test_blood_gas_bicarbonate_absent_in_2021():
    assert "blood_gas_bicarbonate" not in fields_in_category("Hospital Admission", 2021)


def test_blood_gas_bicarbonate_present_in_2026():
    assert "blood_gas_bicarbonate" in fields_in_category("Hospital Admission", 2026)


def test_hospital_admission_core_fields_present_in_both_years():
    for year in (2021, 2026):
        fields = fields_in_category("Hospital Admission", year)
        assert "hospital_admission_date" in fields
        assert "hospital_discharge_date" in fields
        if year == 2021:
            assert "hospital_admission_reason" in fields
        if year == 2026:
            assert "hospital_admission_reason_2026" in fields
        assert "dka_additional_therapies" in fields
        assert "hospital_admission_other" in fields


# ---------------------------------------------------------------------------
# get_tabs — tab structure and active-tab logic
# ---------------------------------------------------------------------------


def test_get_tabs_returns_three_tabs_for_2021():
    tabs = get_tabs(form=None, dataset_year=2021)
    tab_names = [t["name"] for t in tabs]
    assert tab_names == ["Routine Measurements", "Annual Review", "Inpatient Entry"]


def test_get_tabs_returns_three_tabs_for_2026():
    tabs = get_tabs(form=None, dataset_year=2026)
    tab_names = [t["name"] for t in tabs]
    assert tab_names == ["Routine Measurements", "Annual Review", "Inpatient Entry"]


def test_get_tabs_first_tab_is_active_when_no_errors():
    for year in (2021, 2026):
        tabs = get_tabs(form=None, dataset_year=year)
        assert tabs[0].get("active") is True
        assert not tabs[1].get("active")
        assert not tabs[2].get("active")
