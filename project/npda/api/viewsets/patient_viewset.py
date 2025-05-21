from django.apps import apps
from django.db import transaction
from django.utils import timezone

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from oauth2_provider.contrib.rest_framework import TokenHasScope, TokenHasReadWriteScope
from django_filters.rest_framework import DjangoFilterBackend

from project.npda.filtersets.patient_filterset import PatientFilter
from project.npda.models import Patient
from project.npda.api.serializers.patient_serializer import PatientSerializer

class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Patient instances.
    
    This ViewSet provides CRUD operations for Patient records
    Validation is handled by the PatientSerializer.
    The queryset is filtered based on the user's permissions and PDU access.

    Requires OAuth2 authentication with appropriate scopes:
    - GET: 'patient:read' scope
    - POST/PUT/PATCH/DELETE: 'patient:write' scope
    """
    serializer_class = PatientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PatientFilter

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            # Read operations - require read scope
            permission_classes = [TokenHasScope]
            self.required_scopes = ['patient:read']
        else:
            # Write operations - require write scope
            permission_classes = [TokenHasScope]
            self.required_scopes = ['patient:write']
        
        return [permission() for permission in permission_classes]
    
    
    def get_queryset(self):
        """
        Filter patients based on user's permissions and PDU access.
        Additional filtering handled by django-filter.
        """
        user = self.request.user
        
        # Start with all patients
        queryset = Patient.objects.all()
        
        # # Apply PDU filtering for non-superusers
        # if not user.is_superuser and not user.is_rcpch_audit_team_member and not user.is_rcpch_staff:
        #     # Filter by user's PDUs
        #     pdu_codes = user.paediatric_diabetes_units.values_list('pz_code', flat=True)
        #     queryset = queryset.filter(paediatric_diabetes_unit__pz_code__in=pdu_codes)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Create a new patient record with validation and proper associations.
        Using OAuth2 authentication, we check the token scope.
        For session-based authentication, we check the session variable.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """
        Save the patient record with all required associations:
        - Mark patient as valid
        - Associate with PDU
        - Handle transfers if applicable
        - Add to current audit year submission
        """
        # Create the patient and mark as valid
        patient = serializer.save(is_valid=True, errors=None)
        
        # Get models we need
        from django.apps import apps
        PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")
        Transfer = apps.get_model("npda", "Transfer")
        Submission = apps.get_model("npda", "Submission")
        NPDAUser = apps.get_model("npda", "NPDAUser")
        
        # Get the user's PDU
        pz_code = self.request.session.get("pz_code")
        paediatric_diabetes_unit = PaediatricDiabetesUnit.objects.get(pz_code=pz_code)
        
        # Handle transfers if this patient exists in another PDU
        if Transfer.objects.filter(patient=patient).exists():
            # The patient is being transferred from another PDU
            transfer = Transfer.objects.get(patient=patient)
            transfer.previous_pz_code = transfer.paediatric_diabetes_unit.pz_code
            transfer.paediatric_diabetes_unit = paediatric_diabetes_unit
            
            # Get transfer-related data if provided
            date_leaving_service = self.request.data.get("date_leaving_service")
            reason_leaving_service = self.request.data.get("reason_leaving_service")
            
            transfer.date_leaving_service = date_leaving_service
            transfer.reason_leaving_service = reason_leaving_service
            transfer.save()
        else:
            # Create a new transfer record
            Transfer.objects.create(
                paediatric_diabetes_unit=paediatric_diabetes_unit,
                patient=patient,
                date_leaving_service=None,
                reason_leaving_service=None,
            )
        
        # Add patient to current audit period submission
        from project.npda.models import AuditPeriod
        audit_period = AuditPeriod.objects.get_audit_period_for_request(self.request)
        
        submission, created = Submission.objects.update_or_create(
            audit_year=audit_period.audit_year(),
            paediatric_diabetes_unit=paediatric_diabetes_unit,
            submission_active=True,
            defaults={
                "submission_by": NPDAUser.objects.get(pk=self.request.user.pk),
                "submission_date": timezone.now(),
                "audit_period": audit_period
            },
        )
        submission.patients.add(patient)
        submission.save()
    
    def update(self, request, *args, **kwargs):
        """
        Update an existing patient record with validation.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            self.perform_update(serializer)
        
        return Response(serializer.data)
    
    # @action(detail=True, methods=['get'])
    # def visits(self, request, pk=None):
    #     """
    #     Retrieve the visits associated with a specific patient.
    #     """
    #     patient = self.get_object()
        
    #     # This would use a visits serializer that you'd need to create
    #     from project.npda.api.serializers.visit_serializer import VisitSerializer
    #     visits = patient.visit_set.all()
    #     serializer = VisitSerializer(visits, many=True)
        
    #     return Response(serializer.data)
    
    # @action(detail=False, methods=['get'])
    # def recent(self, request):
    #     """
    #     Get the most recently added patients.
    #     """
    #     recent_patients = self.get_queryset().order_by('-id')[:10]
    #     serializer = self.get_serializer(recent_patients, many=True)
    #     return Response(serializer.data)