from ..models import Visit
from rest_framework import viewsets

from ..serializers import VisitSerializer
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
    PolymorphicProxySerializer,
)
from drf_spectacular.types import OpenApiTypes


@extend_schema(
    request=VisitSerializer,
    responses={
        200: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description="Valid Response",
            examples=[
                OpenApiExample(
                    "/visit/1/",
                    external_value="external value",
                    value={"": ""},
                    response_only="true",
                ),
            ],
        ),
    },
    summary="Returns a list of all visits.",
)
class VisitViewSet(viewsets.ModelViewSet):
    queryset = Visit.objects.all()
    serializer_class = VisitSerializer

    def get_view_name(self):
        return "Clinic Visits"

    """
    # GET requests
    Should return:
    1. All visits nationally - Admin only
    2. All visits in a given PDU
    3. All visits for a given child by NHS number
    4. All visits for a given child by visit ID

    Filters
    Should be able to filter by all fields

    # POST requests
    1. Create a new visit against an existing patient (by NHS Number)

    # PUT/PATCH requests
    1. Update a visit by visit ID
    2. Update a visit by NHS number and visit date

    # DELETE
    1. Delete a visit by visit ID
    """
