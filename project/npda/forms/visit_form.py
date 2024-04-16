from django import forms
from django.core.exceptions import ValidationError
from ...constants.styles import *
from ...constants import ALL_VISIT_DATES
from ..general_functions.validate_dates import validate_date
from ..models import Visit


class VisitForm(forms.ModelForm):

    patient = None

    def __init__(self, *args, **kwargs):
        self.patient = kwargs['initial'].get('patient')
        super(VisitForm, self).__init__(*args, **kwargs)

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

    def clean_height(self):
        data = self.cleaned_data["height"]
        if data is not None:
            if data < 40:
                raise ValidationError("Please enter a valid height. Cannot be less than 40cm")
            if data > 240:
                raise ValidationError("Please enter a valid height. Cannot be greater than 240cm")
        return data
    
    
    def clean_visit_date(self):
        data = self.cleaned_data['visit_date']
        valid, error = validate_date(
            date_under_examination_field_name='visit_date',
            date_under_examination_label_name='Visit/Appointment Date',
            date_under_examination=data,
            date_of_birth=self.patient.date_of_birth,
            date_of_diagnosis=self.patient.diagnosis_date,
            date_of_death=self.patient.death_date
        )
        if valid==False:
            raise ValidationError(error)
        
        return self.cleaned_data['visit_date']
    

    def clean_height_weight_observation_date(self):
        data = self.cleaned_data['height_weight_observation_date']
        valid, error = validate_date(
            date_under_examination_field_name='height_weight_observation_date',
            date_under_examination_label_name='Observation Date (Height and weight)',
            date_under_examination=data,
            date_of_birth=self.patient.date_of_birth,
            date_of_diagnosis=self.patient.diagnosis_date,
            date_of_death=self.patient.death_date
        )
        if valid==False:
            raise ValidationError(error)
        
        return self.cleaned_data['height_weight_observation_date']

    def clean_hba1c_date(self):
        data = self.cleaned_data['hba1c_date']
        valid, error = validate_date(
            date_under_examination_field_name='hba1c_date',
            date_under_examination_label_name='Observation Date: Hba1c Value',
            date_under_examination=data,
            date_of_birth=self.patient.date_of_birth,
            date_of_diagnosis=self.patient.diagnosis_date,
            date_of_death=self.patient.death_date
        )
        if valid==False:
            raise ValidationError(error)
        
        return self.cleaned_data['hba1c_date']

    def clean_blood_pressure_observation_date(self):
        data = self.cleaned_data['blood_pressure_observation_date']
        valid, error = validate_date(
            date_under_examination_field_name='blood_pressure_observation_date',
            date_under_examination_label_name='Observation Date (Blood Pressure)',
            date_under_examination=data,
            date_of_birth=self.patient.date_of_birth,
            date_of_diagnosis=self.patient.diagnosis_date,
            date_of_death=self.patient.death_date
        )
        if valid==False:
            raise ValidationError(error)
        
        return self.cleaned_data['blood_pressure_observation_date']

    def clean_foot_examination_observation_date(self):
        data = self.cleaned_data['foot_examination_observation_date']
        valid, error = validate_date(
            date_under_examination_field_name='foot_examination_observation_date',
            date_under_examination_label_name='Foot Assessment / Examination Date',
            date_under_examination=data,
            date_of_birth=self.patient.date_of_birth,
            date_of_diagnosis=self.patient.diagnosis_date,
            date_of_death=self.patient.death_date
        )
        if valid==False:
            raise ValidationError(error)
        
        return self.cleaned_data['foot_examination_observation_date']

    def clean_retinal_screening_observation_date(self):
        data = self.cleaned_data['retinal_screening_observation_date']
        valid, error = validate_date(
            date_under_examination_field_name='retinal_screening_observation_date',
            date_under_examination=data,
            date_under_examination_label_name='Retinal Screening date',
            date_of_birth=self.patient.date_of_birth,
            date_of_diagnosis=self.patient.diagnosis_date,
            date_of_death=self.patient.death_date
        )
        if valid==False:
            raise ValidationError(error)
        
        return self.cleaned_data['retinal_screening_observation_date']

    def clean_albumin_creatinine_ratio_date(self):
        data = self.cleaned_data['albumin_creatinine_ratio_date']
        valid, error = validate_date(
            date_under_examination_field_name='albumin_creatinine_ratio_date',
            date_under_examination_label_name='Observation Date: Urinary Albumin Level',
            date_under_examination=data,
            date_of_birth=self.patient.date_of_birth,
            date_of_diagnosis=self.patient.diagnosis_date,
            date_of_death=self.patient.death_date
        )
        if valid==False:
            raise ValidationError(error)
        
        return self.cleaned_data['albumin_creatinine_ratio_date']

    def clean_total_cholesterol_date(self):
        data = self.cleaned_data['total_cholesterol_date']
        valid, error = validate_date(
            date_under_examination_field_name='total_cholesterol_date',
            date_under_examination_label_name='Observation Date: Total Cholesterol Level',
            date_under_examination=data,
            date_of_birth=self.patient.date_of_birth,
            date_of_diagnosis=self.patient.diagnosis_date,
            date_of_death=self.patient.death_date
        )
        if valid==False:
            raise ValidationError(error)
        
        return self.cleaned_data['total_cholesterol_date']

    def clean_thyroid_function_date(self):
        data = self.cleaned_data['thyroid_function_date']
        valid, error = validate_date(
            date_under_examination_field_name='thyroid_function_date',
            date_under_examination_label_name='Observation Date: Thyroid Function',
            date_under_examination=data,
            date_of_birth=self.patient.date_of_birth,
            date_of_diagnosis=self.patient.diagnosis_date,
            date_of_death=self.patient.death_date
        )
        if valid==False:
            raise ValidationError(error)
        
        return self.cleaned_data['thyroid_function_date']

    def clean_coeliac_screen_date(self):
        data = self.cleaned_data['coeliac_screen_date']
        valid, error = validate_date(
            date_under_examination_field_name='coeliac_screen_date',
            date_under_examination_label_name='Observation Date: Coeliac Disease Screening',
            date_under_examination=data,
            date_of_birth=self.patient.date_of_birth,
            date_of_diagnosis=self.patient.diagnosis_date,
            date_of_death=self.patient.death_date
        )
        if valid==False:
            raise ValidationError(error)
        
        return self.cleaned_data['coeliac_screen_date']

    def clean_psychological_screening_assessment_date(self):
        data = self.cleaned_data['psychological_screening_assessment_date']
        valid, error = validate_date(
            date_under_examination_field_name='psychological_screening_assessment_date',
            date_under_examination_label_name='Observation Date - Psychological Screening Assessment',
            date_under_examination=data,
            date_of_birth=self.patient.date_of_birth,
            date_of_diagnosis=self.patient.diagnosis_date,
            date_of_death=self.patient.death_date
        )
        if valid==False:
            raise ValidationError(error)
        
        return self.cleaned_data['psychological_screening_assessment_date']

    def clean_smoking_cessation_referral_date(self):
        data = self.cleaned_data['smoking_cessation_referral_date']
        valid, error = validate_date(
            date_under_examination_field_name='smoking_cessation_referral_date',
            date_under_examination_label_name='Date of offer of referral to smoking cessation service (if patient is a current smoker)',
            date_under_examination=data,
            date_of_birth=self.patient.date_of_birth,
            date_of_diagnosis=self.patient.diagnosis_date,
            date_of_death=self.patient.death_date
        )
        if valid==False:
            raise ValidationError(error)
        
        return self.cleaned_data['smoking_cessation_referral_date']

    def clean_carbohydrate_counting_level_three_education_date(self):
        data = self.cleaned_data['carbohydrate_counting_level_three_education_date']
        valid, error = validate_date(
            date_under_examination_field_name='carbohydrate_counting_level_three_education_date',
            date_under_examination_label_name='Date of Level 3 carbohydrate counting education received',
            date_under_examination=data,
            date_of_birth=self.patient.date_of_birth,
            date_of_diagnosis=self.patient.diagnosis_date,
            date_of_death=self.patient.death_date
        )
        if valid==False:
            raise ValidationError(error)
        
        return self.cleaned_data['carbohydrate_counting_level_three_education_date']

    def clean_dietician_additional_appointment_date(self):
        data = self.cleaned_data['dietician_additional_appointment_date']
        valid, error = validate_date(
            date_under_examination_field_name='dietician_additional_appointment_date',
            date_under_examination_label_name='Date of additional appointment with dietitian',
            date_under_examination=data,
            date_of_birth=self.patient.date_of_birth,
            date_of_diagnosis=self.patient.diagnosis_date,
            date_of_death=self.patient.death_date
        )
        if valid==False:
            raise ValidationError(error)
        
        return self.cleaned_data['dietician_additional_appointment_date']

    def clean_flu_immunisation_recommended_date(self):
        data = self.cleaned_data['flu_immunisation_recommended_date']
        valid, error = validate_date(
            date_under_examination_field_name='flu_immunisation_recommended_date',
            date_under_examination_label_name='Date that influenza immunisation was recommended',
            date_under_examination=data,
            date_of_birth=self.patient.date_of_birth,
            date_of_diagnosis=self.patient.diagnosis_date,
            date_of_death=self.patient.death_date
        )
        if valid==False:
            raise ValidationError(error)
        
        return self.cleaned_data['flu_immunisation_recommended_date']

    def clean_sick_day_rules_training_date(self):
        data = self.cleaned_data['sick_day_rules_training_date']
        valid, error = validate_date(
            date_under_examination_field_name='sick_day_rules_training_date',
            date_under_examination_label_name="Date of provision of advice ('sick-day rules') about managing diabetes during intercurrent illness or episodes of hyperglycaemia",
            date_under_examination=data,
            date_of_birth=self.patient.date_of_birth,
            date_of_diagnosis=self.patient.diagnosis_date,
            date_of_death=self.patient.death_date
        )
        if valid==False:
            raise ValidationError(error)
        
        return self.cleaned_data['sick_day_rules_training_date']

    def clean_hospital_admission_date(self):
        data = self.cleaned_data['hospital_admission_date']
        valid, error = validate_date(
            date_under_examination_field_name='hospital_admission_date',
            date_under_examination_label_name='Start date (Hospital Provider Spell)',
            date_under_examination=data,
            date_of_birth=self.patient.date_of_birth,
            date_of_diagnosis=self.patient.diagnosis_date,
            date_of_death=self.patient.death_date
        )
        if valid==False:
            raise ValidationError(error)
        
        return self.cleaned_data['hospital_admission_date']

    def clean_hospital_discharge_date(self):
        data = self.cleaned_data['hospital_discharge_date']
        valid, error = validate_date(
            date_under_examination_field_name='hospital_discharge_date',
            date_under_examination_label_name='Discharge date (Hospital provider spell',
            date_under_examination=data,
            date_of_birth=self.patient.date_of_birth,
            date_of_diagnosis=self.patient.diagnosis_date,
            date_of_death=self.patient.death_date
        )
        if valid==False:
            raise ValidationError(error)
        
        return self.cleaned_data['hospital_discharge_date']