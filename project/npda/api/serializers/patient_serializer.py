# Python imports

# DRF imports
from rest_framework import serializers

# RCPCH imports
from project.npda.models import Patient, ETHNICITIES, DIABETES_TYPES, SEX_TYPE
from project.npda.forms.patient_form import PatientForm

class PatientSerializer(serializers.ModelSerializer):
    """
    Serializer for the Patient model.
    Includes all fields from the Patient model and reuses form validation.
    """
    # Use CharField for these fields to ensure proper validation
    nhs_number = serializers.CharField(
        required=False, 
        allow_null=True, 
        allow_blank=True,
        help_text="NHS number for England and Wales patients"
    )
    
    unique_reference_number = serializers.CharField(
        required=False, 
        allow_null=True, 
        allow_blank=True,
        max_length=50,
        help_text="Unique reference number for Jersey patients"
    )
    
    # Explicitly define choice fields to ensure proper validation
    sex = serializers.ChoiceField(
        choices=SEX_TYPE,
        required=False,
        allow_null=True
    )
    
    ethnicity = serializers.ChoiceField(
        choices=ETHNICITIES,
        required=False,
        allow_null=True
    )
    
    diabetes_type = serializers.ChoiceField(
        choices=DIABETES_TYPES,
        required=False,
        allow_null=True
    )
    
    # Define read-only fields
    index_of_multiple_deprivation_quintile = serializers.IntegerField(read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    errors = serializers.JSONField(read_only=True)
    
    # Handle GIS fields - these will be serialized as GeoJSON
    location_wgs = serializers.SerializerMethodField()
    location_bng = serializers.SerializerMethodField()
    location_wgs84 = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = [
            'nhs_number', 'unique_reference_number', 'sex', 'date_of_birth',
            'postcode', 'location_wgs', 'location_bng', 'location_wgs84',
            'ethnicity', 'index_of_multiple_deprivation_quintile', 'diabetes_type',
            'diagnosis_date', 'death_date', 'gp_practice_ods_code', 
            'gp_practice_postcode', 'is_valid', 'errors'
        ]
        read_only_fields = [
            'index_of_multiple_deprivation_quintile', 
            'is_valid', 
            'errors',
            'location_wgs', 'location_bng', 'location_wgs84',
        ]
    
    def get_location_wgs(self, obj):
        """Convert PointField to GeoJSON format for the API"""
        if obj.location_wgs:
            return {
                'type': 'Point',
                'coordinates': [obj.location_wgs.x, obj.location_wgs.y]
            }
        return None
    
    def get_location_bng(self, obj):
        """Convert PointField to GeoJSON format for the API"""
        if obj.location_bng:
            return {
                'type': 'Point',
                'coordinates': [obj.location_bng.x, obj.location_bng.y]
            }
        return None
    
    def get_location_wgs84(self, obj):
        """Convert PointField to GeoJSON format for the API"""
        if obj.location_wgs84:
            return {
                'type': 'Point',
                'coordinates': [obj.location_wgs84.x, obj.location_wgs84.y]
            }
        return None
    
    def validate(self, attrs):
        """
        Use the existing PatientForm validation logic for consistency.
        This ensures API validation matches web form validation exactly.
        """
        # Create a form instance with the data and required context - include the existing instance if available (eg for updates)
        
        form_instance = None
        if self.instance:
            # This is an update operation
            form_instance = self.instance
        form = PatientForm(
            data=attrs,
            instance=form_instance,
            audit_period=self.context.get('audit_period'),
            paediatric_diabetes_unit=self.context.get('paediatric_diabetes_unit'),
            override_postcode=self.context.get('override_postcode', False)
        )
        
        if not form.is_valid():
            # Convert form errors to serializer validation errors
            raise serializers.ValidationError(form.errors)
        
        
        # Store the form's async validation results for use in create/update
        self._form_instance = form
        
        # Return the cleaned data from the form (this includes any modifications
        # made by the external validators)
        return form.cleaned_data
    
    def create(self, validated_data):
        """
        Create a patient instance using the form's save method to ensure
        all the form's post-save logic is executed.
        """
        # Use the form instance we created during validation
        if hasattr(self, '_form_instance'):
            # The form already has the validated data and async results
            instance = self._form_instance.save(commit=False)
            
            # Apply any additional fields that might not be in the form
            for field, value in validated_data.items():
                if hasattr(instance, field):
                    setattr(instance, field, value)
            
            # Mark as valid and save
            instance.is_valid = True
            instance.errors = None
            instance.save()
            
            return instance
        else:
            # Fallback to standard creation if form instance not available
            return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """
        Update a patient instance using the form's save method.
        """
        if hasattr(self, '_form_instance'):
            # The form instance already has the correct instance from validate()
            # and has been validated with the update context
            updated_instance = self._form_instance.save(commit=False)
            
            # Apply any additional fields that might not be in the form
            for field, value in validated_data.items():
                if hasattr(updated_instance, field):
                    setattr(updated_instance, field, value)
            
            # Mark as valid and save
            updated_instance.is_valid = True
            updated_instance.errors = None
            updated_instance.save()
            
            return updated_instance
        else:
            # Fallback to standard update
            return super().update(instance, validated_data)
    
    def _get_srid_for_field(self, field_name):
        """Helper method to get the SRID for a given field"""
        srid_mapping = {
            'location_wgs': 27700,  # British National Grid
            'location_bng': 27700,  # British National Grid
            'location_wgs84': 4326  # WGS 84
        }
        return srid_mapping.get(field_name, 4326)  # Default to WGS 84