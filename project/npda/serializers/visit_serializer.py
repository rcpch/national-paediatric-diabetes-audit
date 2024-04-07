from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from ..models import Visit


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "/patient/1/",
            value={
                "": "",
                "": "",
                "": "",
                "": "",
                "": "",
                "": "",
                "": "",
                "": "",
                "": "",
                "": "",
            },
            response_only=True,
        )
    ]
)
class VisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = "__all__"
        depth = 1
