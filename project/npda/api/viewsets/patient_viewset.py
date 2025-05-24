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
    
    For OAuth2 tokens with PDU profiles, data is automatically scoped to the token's PDU.
    For session-based authentication, data is scoped to the user's assigned PDUs.
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
        Filter patients based on authentication method and PDU access.
        
        For OAuth2 tokens with PDU profiles: Filter to the token's specific PDU
        For session-based authentication: Filter to user's assigned PDUs
        For superusers: Return all patients
        """
        user = self.request.user
        
        # Start with all patients
        queryset = Patient.objects.all()
        
        # Check if this is an OAuth2 request with PDU scoping
        if hasattr(self.request, 'pdu_profile') and self.request.pdu_profile:
            # OAuth2 token with PDU profile - scope to the token's PDU
            pdu = self.request.paediatric_diabetes_unit
            if pdu:
                queryset = queryset.filter(
                    submissions__paediatric_diabetes_unit__pz_code=pdu.pz_code,
                    submissions__paediatric_diabetes_unit__active=True
                )
                # Add debug info for development
                print(f"🔐 OAuth2 PDU scoped query: {pdu.pz_code} ({pdu.lead_organisation_name})")
            else:
                # Token exists but no PDU scoping - return empty queryset for safety
                queryset = queryset.none()
                print("⚠️ OAuth2 token found but no PDU scoping - returning empty queryset")
        
        # Apply PDU filtering for session-based authentication (non-superusers)
        elif not user.is_superuser and not user.is_rcpch_audit_team_member and not user.is_rcpch_staff:
            # Session-based authentication - filter by user's PDUs
            if hasattr(user, 'paediatric_diabetes_units'):
                pdu_codes = user.paediatric_diabetes_units.values_list('pz_code', flat=True)
                queryset = queryset.filter(paediatric_diabetes_unit__pz_code__in=pdu_codes)
                print(f"🔐 Session-based PDU scoped query: {list(pdu_codes)}")
            else:
                # User has no assigned PDUs - return empty queryset
                queryset = queryset.none()
                print("⚠️ Session user has no assigned PDUs - returning empty queryset")
        
        else:
            # Superuser or RCPCH staff - can see all patients
            print(f"🔐 Superuser/RCPCH staff access: {user.email}")
        
        return queryset
    
    def get_pdu_for_request(self):
        """
        Get the PDU for the current request based on authentication method.
        
        Returns:
            PaediatricDiabetesUnit: The PDU to use for this request
        """
        # OAuth2 token with PDU profile
        if hasattr(self.request, 'pdu_profile') and self.request.pdu_profile:
            return self.request.paediatric_diabetes_unit
        
        # Session-based authentication - get from session
        pz_code = self.request.session.get("pz_code")
        if pz_code:
            from django.apps import apps
            PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")
            return PaediatricDiabetesUnit.objects.get(pz_code=pz_code)
        
        return None
    
    def create(self, request, *args, **kwargs):
        """
        Create a new patient record with validation and proper associations.
        PDU is automatically determined from OAuth2 token or session.
        """
        # Validate PDU access before creating
        pdu = self.get_pdu_for_request()
        if not pdu:
            return Response(
                {"detail": "No PDU context available for this request"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
        - Associate with PDU (from OAuth2 token or session)
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
        
        # Get the PDU for this request
        paediatric_diabetes_unit = self.get_pdu_for_request()
        
        if not paediatric_diabetes_unit:
            raise ValueError("No PDU context available for patient creation")
        
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
        
        # Log the creation for audit trail
        print(f"✅ Patient created via {'OAuth2' if hasattr(self.request, 'pdu_profile') else 'session'} "
              f"for PDU {paediatric_diabetes_unit.pz_code}")
    
    def update(self, request, *args, **kwargs):
        """
        Update an existing patient record with validation.
        Ensures the patient belongs to the user's accessible PDUs.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Verify the patient is in the accessible queryset
        if instance not in self.get_queryset():
            return Response(
                {"detail": "You do not have permission to modify this patient record"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            self.perform_update(serializer)
        
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a patient record with PDU scope validation.
        """
        instance = self.get_object()
        
        # Verify the patient is in the accessible queryset
        if instance not in self.get_queryset():
            return Response(
                {"detail": "You do not have permission to delete this patient record"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    # @action(detail=True, methods=['get'])
    # def visits(self, request, pk=None):
    #     """
    #     Retrieve the visits associated with a specific patient.
    #     """
    #     patient = self.get_object()
        
    #     # Verify the patient is accessible
    #     if patient not in self.get_queryset():
    #         return Response(
    #             {"detail": "You do not have permission to access this patient's visits"}, 
    #             status=status.HTTP_403_FORBIDDEN
    #         )
        
    #     # This would use a visits serializer that you'd need to create
    #     from project.npda.api.serializers.visit_serializer import VisitSerializer
    #     visits = patient.visit_set.all()
    #     serializer = VisitSerializer(visits, many=True)
        
    #     return Response(serializer.data)
    
    # @action(detail=False, methods=['get'])
    # def recent(self, request):
    #     """
    #     Get the most recently added patients (scoped to accessible PDUs).
    #     """
    #     recent_patients = self.get_queryset().order_by('-id')[:10]
    #     serializer = self.get_serializer(recent_patients, many=True)
    #     return Response(serializer.data)