from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from project.npda.models import Visit, Patient, PaediatricDiabetesUnit
from project.npda.forms.visit_form import VisitForm
from project.constants import (
    SMOKING_STATUS,
    THYROID_TREATMENT_STATUS,
    CLOSED_LOOP_TYPES,
    HOSPITAL_ADMISSION_REASONS,
    ALBUMINURIA_STAGES,
    YES_NO_UNKNOWN,
    DKA_ADDITIONAL_THERAPIES,
    HBA1C_FORMATS,
    RETINAL_SCREENING_RESULTS,
    TREATMENT_TYPES,
    GLUCOSE_MONITORING_TYPES,
)


class VisitSerializer(serializers.ModelSerializer):
    """
    Serializer for the Visit model in nested patient context.
    Optimized for /patients/{id}/visits/ endpoints.
    Delegates all validation to VisitForm for consistency.
    
    Patient context is implicit from the URL - no need to include in response.
    """
    
    # Choice fields with proper constraints
    smoking_status = serializers.ChoiceField(
        choices=SMOKING_STATUS,
        required=False,
        allow_null=True,
        help_text="Patient's smoking status"
    )
    
    thyroid_treatment_status = serializers.ChoiceField(
        choices=THYROID_TREATMENT_STATUS,
        required=False,
        allow_null=True,
        help_text="Thyroid treatment status"
    )
    
    closed_loop_system = serializers.ChoiceField(
        choices=CLOSED_LOOP_TYPES,
        required=False,
        allow_null=True,
        help_text="Type of closed loop system"
    )
    
    hospital_admission_reason = serializers.ChoiceField(
        choices=HOSPITAL_ADMISSION_REASONS,
        required=False,
        allow_null=True,
        help_text="Reason for hospital admission"
    )
    
    albuminuria_stage = serializers.ChoiceField(
        choices=ALBUMINURIA_STAGES,
        required=False,
        allow_null=True,
        help_text="Stage of albuminuria"
    )
    
    psychological_additional_support_status = serializers.ChoiceField(
        choices=YES_NO_UNKNOWN,
        required=False,
        allow_null=True,
        help_text="Whether psychological additional support was provided"
    )
    
    dietician_additional_appointment_offered = serializers.ChoiceField(
        choices=YES_NO_UNKNOWN,
        required=False,
        allow_null=True,
        help_text="Whether additional dietician appointment was offered"
    )
    
    ketone_meter_training = serializers.ChoiceField(
        choices=YES_NO_UNKNOWN,
        required=False,
        allow_null=True,
        help_text="Whether ketone meter training was provided"
    )
    
    dka_additional_therapies = serializers.ChoiceField(
        choices=DKA_ADDITIONAL_THERAPIES,
        required=False,
        allow_null=True,
        help_text="Additional therapies for DKA treatment"
    )
    
    gluten_free_diet = serializers.ChoiceField(
        choices=YES_NO_UNKNOWN,
        required=False,
        allow_null=True,
        help_text="Whether patient follows gluten-free diet"
    )
    
    hba1c_format = serializers.ChoiceField(
        choices=HBA1C_FORMATS,
        required=False,
        allow_null=True,
        help_text="Format of HbA1c value (mmol/mol or %)"
    )
    
    retinal_screening_result = serializers.ChoiceField(
        choices=RETINAL_SCREENING_RESULTS,
        required=False,
        allow_null=True,
        help_text="Result of retinal screening"
    )
    
    treatment = serializers.ChoiceField(
        choices=TREATMENT_TYPES,
        required=False,
        allow_null=True,
        help_text="Type of diabetes treatment"
    )
    
    glucose_monitoring = serializers.ChoiceField(
        choices=GLUCOSE_MONITORING_TYPES,
        required=False,
        allow_null=True,
        help_text="Type of glucose monitoring"
    )
    
    # Date fields
    visit_date = serializers.DateField(
        required=True,
        help_text="Date of the visit (mandatory field)"
    )
    
    # Read-only calculated fields
    bmi = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        read_only=True,
        help_text="Body Mass Index (calculated automatically)"
    )
    
    height_centile = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        read_only=True,
        help_text="Height centile (calculated automatically)"
    )
    
    weight_centile = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        read_only=True,
        help_text="Weight centile (calculated automatically)"
    )
    
    bmi_centile = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        read_only=True,
        help_text="BMI centile (calculated automatically)"
    )

    class Meta:
        model = Visit
        fields = [
            # Visit identification
            'id',
            
            # Core visit data
            'visit_date',
            'height',
            'weight',
            'bmi',
            'height_weight_observation_date',
            'hba1c',
            'hba1c_format',
            'hba1c_date',
            'treatment',
            'closed_loop_system',
            'glucose_monitoring',
            'systolic_blood_pressure',
            'diastolic_blood_pressure',
            'blood_pressure_observation_date',
            'foot_examination_observation_date',
            'retinal_screening_observation_date',
            'retinal_screening_result',
            'albumin_creatinine_ratio',
            'albumin_creatinine_ratio_date',
            'albuminuria_stage',
            'total_cholesterol',
            'total_cholesterol_date',
            'thyroid_function_date',
            'thyroid_treatment_status',
            'coeliac_screen_date',
            'gluten_free_diet',
            'psychological_screening_assessment_date',
            'psychological_additional_support_status',
            'smoking_status',
            'smoking_cessation_referral_date',
            'carbohydrate_counting_level_three_education_date',
            'dietician_additional_appointment_offered',
            'dietician_additional_appointment_date',
            'flu_immunisation_recommended_date',
            'ketone_meter_training',
            'sick_day_rules_training_date',
            'hospital_admission_date',
            'hospital_discharge_date',
            'hospital_admission_reason',
            'dka_additional_therapies',
            'hospital_admission_other',
            
            # Calculated centiles (read-only)
            'height_centile',
            'weight_centile',
            'bmi_centile',
        ]
        read_only_fields = [
            'id',
            'bmi',
            'height_centile', 
            'weight_centile', 
            'bmi_centile',
        ]
    
    def validate(self, attrs):
        """
        Use VisitForm validation for all business logic validation.
        Patient is provided from the URL context, not from POST data.
        """
        # Get patient from the viewset context (set by get_patient() method)
        patient = self.context.get('patient')
        
        if not patient and not self.instance:
            # This should not happen if the viewset is set up correctly
            raise serializers.ValidationError({
                'patient': 'Patient context not available. This visit must be created through /patients/{id}/visits/ endpoint.'
            })
        
        # For updates, use the existing patient
        if self.instance:
            patient = self.instance.patient
        
        # Verify PDU access if context is available
        user_pdu = self.context.get('paediatric_diabetes_unit')
        if user_pdu and patient:
            from project.npda.models import Transfer
            
            patient_pdus = Transfer.objects.filter(
                patient=patient,
                date_leaving_service__isnull=True  # Active transfers
            ).values_list('paediatric_diabetes_unit', flat=True)
            
            if user_pdu.pk not in patient_pdus:
                raise serializers.ValidationError({
                    'patient': 'Patient is not accessible within your PDU scope'
                })
        
        # Create VisitForm with patient in initial data
        form_data = attrs.copy()
        form_initial = {'patient': patient}
        
        # Create form instance
        form_instance = self.instance if self.instance else None
        
        form = VisitForm(
            data=form_data,
            initial=form_initial,
            instance=form_instance,
        )
        
        # Run form validation - this will call all the clean methods and external validators
        if not form.is_valid():
            # Convert form errors to serializer validation errors
            form_errors = {}
            for field, errors in form.errors.items():
                if field == '__all__':
                    # Non-field errors
                    form_errors['non_field_errors'] = errors
                else:
                    form_errors[field] = errors
            
            raise serializers.ValidationError(form_errors)
        
        # Store the validated form instance for use in create/update
        self._validated_form = form
        
        # Return the cleaned data from the form plus the patient
        cleaned_data = form.cleaned_data.copy()
        cleaned_data['patient'] = patient
        
        return cleaned_data
    
    def create(self, validated_data):
        """
        Create a visit instance using the form's save method to ensure
        all external validation and calculations are applied.
        """
        if hasattr(self, '_validated_form'):
            return self._validated_form.save()
        else:
            return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """
        Update a visit instance using the form's save method.
        """
        if hasattr(self, '_validated_form'):
            return self._validated_form.save()
        else:
            return super().update(instance, validated_data)