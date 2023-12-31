from ..models import Patient
from rest_framework import viewsets

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
    PolymorphicProxySerializer,
)
from drf_spectacular.types import OpenApiTypes


from ..serializers import PatientSerializer


# ViewSets define the view behavior.
class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer

    def get_view_name(self):
        return "Patients"


"""
    # GET requests
    Should return:
    1. All patients nationally - Admin only
    2. All patients in a given PDU
    3. A given child by NHS number
    4. A given child by patient ID

    Filters
    Should be able to filter by all fields

    # POST requests
    1. Create a new child

    # PUT/PATCH requests
    1. Update a child by patient ID
    2. Update a child by NHS number

    # DELETE
    1. Delete a child by patient ID
    2. Delete a child by NHS Number
    (cascades to delete all related visits)
    """
