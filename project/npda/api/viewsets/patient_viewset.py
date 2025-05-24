from django.apps import apps
from django.db import transaction
from django.utils import timezone
import logging

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from oauth2_provider.contrib.rest_framework import TokenHasScope, TokenHasReadWriteScope
from django_filters.rest_framework import DjangoFilterBackend

from project.npda.filtersets.patient_filterset import PatientFilter
from project.npda.models import Patient, AuditPeriod,Transfer, Submission, NPDAUser
from project.npda.api.serializers.patient_serializer import PatientSerializer
from project.npda.general_functions import get_audit_period_for_date
from project.npda.api.response_metadata import NPDAResponseMixin

logger = logging.getLogger(__name__)

class PatientViewSet(NPDAResponseMixin, viewsets.ModelViewSet):
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

        This creates a new patient record, ensuring:
        - The patient is valid and has no errors
        - The patient is associated with the correct PDU
        - The patient is added to the current audit year submission
        - NHS Number and Unique Reference Number are unique within the submission
        - Handles transfers if the patient exists in another PDU
        - Validates that there is an active audit period for this request
        **In future other audit years may be supported, but currently only the current audit year is used.**
        """
        # Validate PDU access before creating
        pdu = self.get_pdu_for_request()
        if not pdu:
            return Response(
                {"detail": "No PDU context available for this request"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check there is an active audit period for this request
        active_audit_dates = get_audit_period_for_date(timezone.now())
        audit_period = AuditPeriod.objects.filter(
            start_date__year=active_audit_dates[0].year,
            end_date__year=active_audit_dates[1].year,
        ).first()
        if not audit_period:
            return Response(
                {"detail": "No active audit period found for this request"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use select_for_update to prevent race conditions during the check
        with transaction.atomic():            
            # Continue with normal creation inside the same transaction
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                self.perform_create(serializer)
            else:
                return Response(
                    serializer.errors, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Check if we created a new submission
            submission_created = getattr(self, '_submission_created', False)
            submission_id = getattr(self, '_submission_id', None)
            advisory_message = None
            if submission_created:
                advisory_message = f'New submission {submission_id} created for current audit period'
            else:
                advisory_message = f'Patient added to existing submission {submission_id} for current audit period'
        
        return self.create_npda_response(
            data=serializer.data,
            status=status.HTTP_201_CREATED,
            advisory_message=advisory_message if advisory_message is not None else None,
            advisory_type='info'
        )

    def perform_create(self, serializer):
        """
        Save the patient record with all required associations:
        - Mark patient as valid
        - Associate with PDU (from OAuth2 token or session)
        - Handle transfers if applicable
        - Add to current audit year submission
        
        All operations are wrapped in a transaction to ensure atomicity.
        If any step fails, the entire operation is rolled back.
        """
        # Get the PDU for this request first (before transaction)
        paediatric_diabetes_unit = self.get_pdu_for_request()
        
        if not paediatric_diabetes_unit:
            raise ValueError("No PDU context available for patient creation")
        
        # Get audit period before transaction
        current_audit_period = get_audit_period_for_date(timezone.now())
        audit_period = AuditPeriod.objects.filter(
            start_date__year=current_audit_period[0].year,
            end_date__year=current_audit_period[1].year,
        ).first()
        
        if not audit_period:
            raise ValueError("No active audit period found for this request")
        
        # Wrap all database operations in a transaction - do not want to save a patient without an associated Submission or Transfer
        with transaction.atomic():
            try:
                # Step 1: Create the patient
                patient = serializer.save()
                logger.info(f"📝 Patient {patient.nhs_number} created, proceeding with associations...")
                
                # Step 2: Handle transfers
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
                    logger.info(f"🔄 Transfer updated for patient {patient.nhs_number}")
                else:
                    # Create a new transfer record
                    transfer = Transfer.objects.create(
                        paediatric_diabetes_unit=paediatric_diabetes_unit,
                        patient=patient,
                        date_leaving_service=None,
                        reason_leaving_service=None,
                    )
                    logger.info(f"📋 New transfer created for patient {patient.nhs_number}")
                
                # Step 3: Get or create the submission
                submission, created = Submission.objects.update_or_create(
                    paediatric_diabetes_unit=paediatric_diabetes_unit,
                    audit_period=audit_period,
                    submission_active=True,
                    defaults={
                        'submission_date': timezone.now(),
                        'submission_by': NPDAUser.objects.get(pk=self.request.user.pk),
                        'audit_year': audit_period.audit_year() if hasattr(audit_period, 'audit_year') else timezone.now().year,
                    }
                )
                logger.info(f"📊 Submission {'created' if created else 'found'}: {submission.id}")
                
                # Step 4: Add patient to submission
                submission.patients.add(patient)
                logger.info(f"✅ Patient {patient.nhs_number} added to submission {submission.id}")
                
                # Step 5: Verify the patient was properly added
                if not submission.patients.filter(id=patient.id).exists():
                    raise ValueError(f"Failed to add patient {patient.nhs_number} to submission {submission.id}")
                
                # Store for response generation
                self._submission_created = created
                self._submission_id = submission.id
                
                # Log successful completion
                logger.info(f"✅ Patient {patient.nhs_number} successfully created with all associations "
                        f"via {'OAuth2' if hasattr(self.request, 'pdu_profile') else 'session'} "
                        f"for PDU {paediatric_diabetes_unit.pz_code}")
                
            except Exception as e:
                # Log the error for debugging
                logger.error(f"❌ Failed to create patient with all associations: {str(e)}")
                
                # Re-raise the exception to trigger transaction rollback
                # The transaction.atomic() will automatically rollback all changes
                raise ValueError(f"Failed to create patient record with required associations: {str(e)}")
    
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
    
    def get_serializer_context(self):
        """
        Provide context needed for form validation in the serializer.
        """
        context = super().get_serializer_context()
        
        # Add PDU context
        pdu = self.get_pdu_for_request()
        if pdu:
            context['paediatric_diabetes_unit'] = pdu
        
        # Add audit year context
        from project.npda.models import AuditPeriod
        from project.npda.models import AuditPeriod
        active_audit_dates = get_audit_period_for_date(timezone.now())
        audit_period = AuditPeriod.objects.filter(
            start_date__year=active_audit_dates[0].year,
            end_date__year=active_audit_dates[1].year,
        ).first()
        if not audit_period:
            return Response(
                {"detail": "No active audit period found for this request"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        context['audit_period'] = audit_period
        
        # Add override_postcode flag from request data
        context['override_postcode'] = self.request.data.get('override_postcode', False)
        
        return context
    
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