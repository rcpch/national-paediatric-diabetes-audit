from ..models import Visit
from rest_framework import viewsets

from ..serializers import VisitSerializer


# ViewSets define the view behavior.
class VisitViewSet(viewsets.ModelViewSet):
    queryset = Visit.objects.all()
    serializer_class = VisitSerializer

    def get_view_name(self):
        return "Clinic Visits"