from rest_framework import serializers
from ..models import PaediatricDiabetesUnit, Organisation


class OrganisationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Organisation
        fields = "__all__"

class PDUSerializer(serializers.ModelSerializer):
    organisation = serializers.StringRelatedField(many=False)
    class Meta:
        model = PaediatricDiabetesUnit
        fields = ('organisation', 'pz_code')
