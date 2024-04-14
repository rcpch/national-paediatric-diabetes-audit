from django import forms
from ..models import Visit
from ...constants.styles import *


class VisitForm(forms.ModelForm):

    class Meta:
        model = Visit
        fields = [
            "visit_date",
            "height",
            "weight",
            "height_weight_observation_date",
            "hba1c",
            "hba1c_format",
            "hba1c_date",
            "treatment",
            "closed_loop_system",
            "glucose_monitoring",
            "systolic_blood_pressure",
            "diastolic_blood_pressure",
            "blood_pressure_observation_date",
            "foot_examination_observation_date",
            "retinal_screening_observation_date",
            "retinal_screening_result",
            "albumin_creatinine_ratio",
            "albumin_creatinine_ratio_date",
            "albuminuria_stage",
            "total_cholesterol",
            "total_cholesterol_date",
            "thyroid_function_date",
            "thyroid_treatment_status",
            "coeliac_screen_date",
            "gluten_free_diet",
            "psychological_screening_assessment_date",
            "psychological_additional_support_status",
            "smoking_status",
            "smoking_cessation_referral_date",
            "carbohydrate_counting_level_three_education_date",
            "dietician_additional_appointment_offered",
            "dietician_additional_appointment_date",
            "flu_immunisation_recommended_date",
            "ketone_meter_training",
            "sick_day_rules_training_date",
            "hospital_admission_date",
            "hospital_discharge_date",
            "hospital_admission_reason",
            "dka_additional_therapies",
            "hospital_admission_other",
        ]

        widgets = {
            "visit_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "height": forms.TextInput(attrs={"class": TEXT_INPUT}),
            "weight": forms.TextInput(attrs={"class": TEXT_INPUT}),
            "height_weight_observation_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "hba1c": forms.TextInput(attrs={"class": TEXT_INPUT}),
            "hba1c_format": forms.Select(attrs={"class": SELECT}),
            "hba1c_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "treatment": forms.Select(attrs={"class": SELECT}),
            "closed_loop_system": forms.Select(attrs={"class": SELECT}),
            "glucose_monitoring": forms.Select(attrs={"class": SELECT}),
            "systolic_blood_pressure": forms.TextInput(attrs={"class": TEXT_INPUT}),
            "diastolic_blood_pressure": forms.TextInput(attrs={"class": TEXT_INPUT}),
            "blood_pressure_observation_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "foot_examination_observation_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "retinal_screening_observation_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "retinal_screening_result": forms.Select(attrs={"class": SELECT}),
            "albumin_creatinine_ratio": forms.TextInput(attrs={"class": TEXT_INPUT}),
            "albumin_creatinine_ratio_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "albuminuria_stage": forms.Select(attrs={"class": SELECT}),
            "total_cholesterol": forms.TextInput(attrs={"class": TEXT_INPUT}),
            "total_cholesterol_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "thyroid_function_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "thyroid_treatment_status": forms.Select(attrs={"class": SELECT}),
            "coeliac_screen_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "gluten_free_diet": forms.Select(attrs={"class": SELECT}),
            "psychological_screening_assessment_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "psychological_additional_support_status": forms.Select(
                attrs={"class": SELECT}
            ),
            "smoking_status": forms.Select(attrs={"class": SELECT}),
            "smoking_cessation_referral_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "carbohydrate_counting_level_three_education_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "dietician_additional_appointment_offered": forms.Select(
                attrs={"class": SELECT}
            ),
            "dietician_additional_appointment_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "flu_immunisation_recommended_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "ketone_meter_training": forms.Select(attrs={"class": SELECT}),
            "sick_day_rules_training_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "hospital_admission_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "hospital_discharge_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "hospital_admission_reason": forms.Select(attrs={"class": SELECT}),
            "dka_additional_therapies": forms.Select(attrs={"class": SELECT}),
            "hospital_admission_other": forms.TextInput(attrs={"class": TEXT_INPUT}),
        }
    
