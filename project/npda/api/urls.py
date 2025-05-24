from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets.patient_viewset import PatientViewSet

# Use a clear namespace to avoid conflicts
app_name = 'api'

# Use explicit URL patterns with completely different names from web app
urlpatterns = [
    # API endpoints with unique names (prefixed with 'api_')
    path('v1/patients/', PatientViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='api_patient_list'),
    
    path('v1/patients/<str:pk>/', PatientViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='api_patient_detail'),
    
    # OAuth2 and auth endpoints
    path('v1/oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('v1/auth/', include('rest_framework.urls', namespace='rest_framework')),
]