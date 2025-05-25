from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets.patient_viewset import PatientViewSet

# Use a clear namespace to avoid conflicts
app_name = 'api'

# Use explicit URL patterns with completely different names from web app
urlpatterns = [
    # API endpoints with unique names (prefixed with 'api_')
    path('patients/', PatientViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='api_patient_list'),
    
    path('patients/<str:pk>/', PatientViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='api_patient_detail'),
    
    # OAuth2 and auth endpoints
    path('oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]