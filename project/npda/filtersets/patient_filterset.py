from django_filters.rest_framework import DjangoFilterBackend, FilterSet, ChoiceFilter, CharFilter, DateFilter

from project.npda.models import Patient, DIABETES_TYPES
from project.npda.api.serializers.patient_serializer import PatientSerializer


class PatientFilter(FilterSet):
    """
    Filter class for the Patient model.
    Provides filters for common search fields.
    """
    diabetes_type = ChoiceFilter(choices=DIABETES_TYPES)
    nhs_number = CharFilter(lookup_expr='icontains')
    unique_reference_number = CharFilter(lookup_expr='icontains')
    diagnosis_date_after = DateFilter(field_name='diagnosis_date', lookup_expr='gte')
    diagnosis_date_before = DateFilter(field_name='diagnosis_date', lookup_expr='lte')
    
    class Meta:
        model = Patient
        fields = [
            'diabetes_type', 
            'nhs_number', 
            'unique_reference_number',
            'sex', 
            'ethnicity',
            'diagnosis_date_after',
            'diagnosis_date_before'
        ]
