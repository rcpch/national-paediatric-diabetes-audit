from rest_framework import serializers
from django.contrib.gis.geos import Point
from project.npda.models import Patient, ETHNICITIES, DIABETES_TYPES, SEX_TYPE
from project.npda.forms.patient_form import PatientForm


class PatientSerializer(serializers.ModelSerializer):
    """
    Serializer for the Patient model.
    Includes all fields from the Patient model and reuses form validation.
    """
    # Define the read-only fields
    index_of_multiple_deprivation_quintile = serializers.IntegerField(read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    errors = serializers.JSONField(read_only=True)
    location_wgs = serializers.SerializerMethodField(read_only=True)
    location_bng = serializers.SerializerMethodField(read_only=True)
    location_wgs84 = serializers.SerializerMethodField(re
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
        write_only_fields = ['nhs_number', 'unique_reference_number', 'sex', 'date_of_birth',
            'postcode','ethnicity','diabetes_type',
            'diagnosis_date', 'death_date', 'gp_practice_ods_code', 
            'gp_practice_postcode']  # If needed
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
    Reuse existing form validation logic and validate postcode using the API
    """
     # Check for presence of identifiers - either NHS number or Unique Reference Number
    # At least one of these must be provided, but not both
    has_nhs = attrs.get('nhs_number') not in (None, '')
    has_urn = attrs.get('unique_reference_number') not in (None, '')
    
    # Validate identifier requirements
    if not (has_nhs or has_urn):
        raise serializers.ValidationError({
            "identifier": "Either NHS number or Unique Reference Number must be provided."
        })
    
    if has_nhs and has_urn:
        raise serializers.ValidationError({
            "identifier": "Cannot provide both NHS number and Unique Reference Number."
        })

    # Create a copy of attrs to avoid modifying the original
    data = attrs.copy()
    # Use existing form validation logic
    form = PatientForm(data=data)
    if not form.is_valid():
        raise serializers.ValidationError(form.errors)
        
    return data  # Return modified data with updated postcode and location fields
    
    def _get_srid_for_field(self, field_name):
        """Helper method to get the SRID for a given field"""
        srid_mapping = {
            'location_wgs': 27700,  # British National Grid
            'location_bng': 27700,  # British National Grid
            'location_wgs84': 4326  # WGS 84
        }
        return srid_mapping.get(field_name, 4326)  # Default to WGS 84