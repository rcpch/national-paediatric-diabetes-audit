from rest_framework import serializers
from ..models import Visit


# Serializers define the API representation.
class VisitSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Visit
        fields = "__all__"
        depth = 1
