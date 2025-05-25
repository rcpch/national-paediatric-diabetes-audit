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
        # Get patient from context (set by viewset)
        patient = self.context.get('patient')
        
        if not patient:
            raise serializers.ValidationError({
                'patient': 'Patient context not available. This visit must be created through /api/v1/patients/{id}/visits/ endpoint.'
            })
        
        # Prepare initial data with just the patient
        initial_data = {
            'patient': patient,
        }
        
        # Create the form with proper initial data
        if self.instance:
            # For updates
            form = VisitForm(
                data=attrs,
                initial=initial_data,
                instance=self.instance
            )
        else:
            # For creates
            form = VisitForm(
                data=attrs,
                initial=initial_data
            )
        
        if not form.is_valid():
            # Convert form errors to DRF format
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = field_errors
            if form.non_field_errors():
                errors['non_field_errors'] = form.non_field_errors()
            raise serializers.ValidationError(errors)
        
        # Store the validated form to use in create/update
        self._validated_form = form
        
        return attrs
    
    def create(self, validated_data):
        """
        Create a visit instance using the form's validated data.
        Patient comes from the context.
        """
        # Get patient from context
        patient = self.context.get('patient')
        
        if not patient:
            raise serializers.ValidationError({
                'patient': 'Patient context not available. This visit must be created through /api/v1/patients/{id}/visits/ endpoint.'
            })
        
        # Check if we have the validated form from the validate() method
        if hasattr(self, '_validated_form'):
            # Get the cleaned data from the form validation
            cleaned_data = self._validated_form.cleaned_data.copy()
            
            # Add the patient foreign key to the cleaned data
            cleaned_data['patient'] = patient
            
            # Create the visit instance using the cleaned form data
            visit = Visit.objects.create(**cleaned_data)
            
            # Copy any calculated fields from the form's async validation results
            if hasattr(self._validated_form, 'async_validation_results') and self._validated_form.async_validation_results:
                results = self._validated_form.async_validation_results
                
                # Set BMI if calculated
                if hasattr(results, 'bmi') and results.bmi:
                    visit.bmi = results.bmi
                
                # Set centiles if calculated
                for field_prefix in ['height', 'weight', 'bmi']:
                    result = getattr(results, f'{field_prefix}_result', None)
                    if result and not isinstance(result, Exception):
                        if hasattr(result, 'centile'):
                            setattr(visit, f'{field_prefix}_centile', result.centile)
                        if hasattr(result, 'sds'):
                            setattr(visit, f'{field_prefix}_sds', result.sds)
                
                # Save the visit with calculated fields
                visit.save()
            
            return visit
        else:
            # This shouldn't happen if validate() was called properly
            raise serializers.ValidationError({
                'non_field_errors': 'Form validation failed. Please check all required fields.'
            })
    
    def update(self, instance, validated_data):
        """
        Update a visit instance using the form's validated data.
        Patient relationship should not change during updates.
        """
        # Check if we have the validated form from the validate() method
        if hasattr(self, '_validated_form'):
            # Get the cleaned data from the form validation
            cleaned_data = self._validated_form.cleaned_data.copy()
            
            # Remove patient from cleaned_data if it exists (patient shouldn't change)
            cleaned_data.pop('patient', None)
            
            # Update the instance with cleaned data
            for field, value in cleaned_data.items():
                if hasattr(instance, field):
                    setattr(instance, field, value)
            
            # Copy any calculated fields from the form's async validation results
            if hasattr(self._validated_form, 'async_validation_results') and self._validated_form.async_validation_results:
                results = self._validated_form.async_validation_results
                
                # Set BMI if calculated
                if hasattr(results, 'bmi') and results.bmi:
                    instance.bmi = results.bmi
                
                # Set centiles if calculated
                for field_prefix in ['height', 'weight', 'bmi']:
                    result = getattr(results, f'{field_prefix}_result', None)
                    if result and not isinstance(result, Exception):
                        if hasattr(result, 'centile'):
                            setattr(instance, f'{field_prefix}_centile', result.centile)
                        if hasattr(result, 'sds'):
                            setattr(instance, f'{field_prefix}_sds', result.sds)
            
            # Save the updated instance
            instance.save()
            return instance
        else:
            # Fallback to standard DRF update
            return super().update(instance, validated_data)