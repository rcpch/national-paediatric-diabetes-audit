from ..models import PaediatricDiabetesUnit
from rest_framework import viewsets

from ..serializers import PDUSerializer


# ViewSets define the view behavior.
class PDUViewSet(viewsets.ModelViewSet):
    queryset = PaediatricDiabetesUnit.objects.all()
    serializer_class = PDUSerializer

    def get_view_name(self):
        return "Paediatric Diabetes Units"