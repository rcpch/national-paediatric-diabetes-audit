from ..models import Patient
from rest_framework import viewsets

from ..serializers import PatientSerializer


# ViewSets define the view behavior.
class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer

    def get_view_name(self):
        return "Patients"