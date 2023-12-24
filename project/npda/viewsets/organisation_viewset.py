from ..models import Organisation
from rest_framework import viewsets

from ..serializers import OrganisationSerializer


# ViewSets define the view behavior.
class OrganisationViewSet(viewsets.ModelViewSet):
    queryset = Organisation.objects.all()
    serializer_class = OrganisationSerializer

    def get_view_name(self):
        return "Organisations"
