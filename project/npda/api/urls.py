from django.urls import path, include
from .viewsets.patient_viewset import PatientViewSet
from .viewsets.visit_viewset import VisitViewSet
# Use a clear namespace to avoid conflicts
app_name = 'api'

# Use explicit URL patterns with completely different names from web app
urlpatterns = [
    # Patient API endpoints
    path('patients/', PatientViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='api_patient_list'),
    
    path('patients/<str:pk>/', PatientViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        # 'delete': 'destroy' # DESTRUCTIVE METHOD: Uncomment if needed
    }), name='api_patient_detail'),

    # Nested Visit endpoints under patients
    path('patients/<str:patient_pk>/visits/', VisitViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='api_patient_visits'),
    
    path('patients/<str:patient_pk>/visits/<int:pk>/', VisitViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update'
    }), name='api_patient_visit_detail'),
    
    # OAuth2 and auth endpoints
    path('oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]