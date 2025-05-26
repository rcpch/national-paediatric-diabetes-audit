# python imports
import logging

# django imports
from django.apps import apps
from django.db import transaction
from django.http import Http404
from django.utils import timezone

# django rest framework imports
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

# third-party imports
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

# RCPCH imports
from project.npda.api.permissions import TokenHasPatientScopeAndPDUAccess
from project.npda.api.authentication_class import PDUScopedOAuth2Authentication
from project.npda.filtersets.patient_filterset import PatientFilter
from project.npda.models import Patient, AuditPeriod,Transfer, Submission, NPDAUser, PaediatricDiabetesUnit
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
    authentication_classes = [PDUScopedOAuth2Authentication]
    permission_classes = [TokenHasPatientScopeAndPDUAccess]

    # Only allow read and write operations, no delete
    http_method_names = ['get', 'post', 'put', 'patch', 'options', 'head']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            # Read operations - require read scope
            permission_classes = [TokenHasPatientScopeAndPDUAccess]
            self.required_scopes = ['patient:read']
        else:
            # Write operations - require write scope
            permission_classes = [TokenHasPatientScopeAndPDUAccess]
            self.required_scopes = ['patient:write']
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Return all patients - permission class handles PDU scoping.
        """
        current_audit_dates = get_audit_period_for_date(timezone.now())
        audit_period = AuditPeriod.objects.filter(
            start_date = current_audit_dates[0],
            end_date = current_audit_dates[1],
            is_open=True,
            is_visible=True,
        ).first()
        pdu = self.get_pdu_for_request()
        
        if Submission.objects.filter(
            submission_active=True,
            audit_period=audit_period,
        ).exists():
            # Get PDU context
            if hasattr(self.request.auth, 'scope') and self.request.auth.scope:
                token_scopes = self.request.auth.scope.split()
                if 'admin:cross-pdu' in token_scopes:
                    # Get the current submission for the active audit period
                    current_submission = Submission.objects.filter(
                        submission_active=True,
                        audit_period=audit_period,
                    ).first()
                else:
                    # For session-based authentication, use the PDU from the request
                    if pdu:
                        current_submission = Submission.objects.filter(
                            paediatric_diabetes_unit=pdu,
                            submission_active=True,
                            audit_period=audit_period,
                        ).first()
                    else:
                        raise Http404("No PDU context available for this request")

                return  current_submission.patients.all()
            
            logger.warning("No active submission found for the current audit period within the PDU scope")
            return Patient.objects.none()  # No active submission found for the current audit period
        else:
            # No active submission for the current audit period
            logger.warning("No active submission found for the current audit period")
            return Patient.objects.none()
        
    def get_pdu_for_request(self):
        """
        Get the PDU for the current request based on authentication method.
        
        Returns:
            PaediatricDiabetesUnit: The PDU to use for this request
        """
        # OAuth2 token with PDU profile
        if hasattr(self.request, 'pdu_profile') and self.request.pdu_profile:
            return self.request.paediatric_diabetes_unit
        
        return None
    
    @extend_schema(
        responses={
            200: PatientSerializer(many=True),
            400: 'Bad Request',
            403: 'Forbidden',
            404: 'Not Found',
            500: 'Internal Server Error'
        },
        operation_id='listPatients',
        summary='List all patients in the current PDU\'s active submission for the current audit period.',
        description='This endpoint retrieves all patients associated with the current PDU\'s active submission for the current audit period. It applies any query parameters using the PatientFilter.',
        tags=['Patients'],
    )
    def list(self, request, *args, **kwargs):
        """
        List all patients in the current PDU's active submission for the current audit period.
        Uses the PatientFilter to apply any query parameters.
        """
        logger.info(f"🔍 Listing patients for PDU {self.get_pdu_for_request().pz_code if self.get_pdu_for_request() else 'unknown'}")
        queryset = self.filter_queryset(self.get_queryset())
        
        # Serialize the queryset
        serializer = self.get_serializer(queryset, many=True)
        
        return self.create_npda_response(
            data=serializer.data,
            status=status.HTTP_200_OK,
            advisory_message=f"{queryset.count()} patients list retrieved successfully",
            advisory_type='info'
        )
   
    @extend_schema(
        responses={
            200: PatientSerializer,
            400: 'Bad Request',
            403: 'Forbidden',
            404: 'Not Found',
            500: 'Internal Server Error'
        },
        operation_id='retrievePatient',
        summary='Retrieve a single patient record by NHS Number or Unique Reference Number.',
        description='This endpoint retrieves a single patient record by NHS Number or Unique Reference Number. The patient must be associated with the current PDU\'s active submission for the current audit period.',
        tags=['Patients'],
    )
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single patient record by NHS Number or Unique Reference Number.
        The patient must be associated with the current PDU's active submission for the current audit period.
        """
        logger.info(f"🔍 Retrieving patient with identifier {kwargs.get('pk')} for PDU {self.get_pdu_for_request().pz_code if self.get_pdu_for_request() else 'unknown'}")
        instance = self.get_object()
        
        # Serialize the instance
        serializer = self.get_serializer(instance)
        
        return self.create_npda_response(
            data=serializer.data,
            status=status.HTTP_200_OK,
            advisory_message=f"Patient {instance.nhs_number} retrieved successfully",
            advisory_type='info'
        )

    @extend_schema(
        request=PatientSerializer,
        responses={
            201: PatientSerializer,
            400: 'Bad Request',
            403: 'Forbidden',
            404: 'Not Found',
            500: 'Internal Server Error'
        },
        operation_id='createPatient',
        summary='Create a new patient record in the current PDU\'s active submission for the current audit period.',
        description='This endpoint creates a new patient record, ensuring that the patient is valid and has no errors. The patient is associated with the correct PDU and added to the current audit year submission. NHS Number and Unique Reference Number are validated for uniqueness within the submission. Handles transfers if the patient exists in another PDU. Validates that there is an active audit period for this request.',
        tags=['Patients'],
    )
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
    
    @extend_schema(
        request=PatientSerializer,
        responses={
            200: PatientSerializer,
            400: 'Bad Request',
            403: 'Forbidden',
            404: 'Not Found',
            500: 'Internal Server Error'
        },
        operation_id='updatePatient',
        summary='Update an existing patient record in the current PDU\'s active submission for the current audit period.',
        description='This endpoint updates an existing patient record, ensuring that the patient is valid and has no errors. The patient must be associated with the correct PDU and the update will be applied to the current audit year submission. NHS Number and Unique Reference Number are validated for uniqueness within the submission. Handles transfers if the patient exists in another PDU. Validates that there is an active audit period for this request.',
        tags=['Patients'],
    )
    def update(self, request, *args, **kwargs):
        """
        Handle PUT requests for full patient record updates.
        All required fields must be provided.
        """
        logger.info(f"🔄 PUT request for patient update by user {request.user.id}")
        return self._perform_update(request, partial=False, method="PUT", *args, **kwargs)
    
    @extend_schema(
        request=PatientSerializer,
        responses={
            200: PatientSerializer,
            400: 'Bad Request',
            403: 'Forbidden',
            404: 'Not Found',
            500: 'Internal Server Error'
        },
        operation_id='partialUpdatePatient',
        summary='Partially update an existing patient record in the current PDU\'s active submission for the current audit period.',
        description='This endpoint partially updates an existing patient record, allowing only provided fields to be updated. The patient must be associated with the correct PDU and the update will be applied to the current audit year submission. NHS Number and Unique Reference Number are validated for uniqueness within the submission. Handles transfers if the patient exists in another PDU. Validates that there is an active audit period for this request.',
        tags=['Patients'],
    )
    def partial_update(self, request, *args, **kwargs):
        """
        Handle PATCH requests for partial patient record updates.
        Only provided fields will be updated.
        """
        return self._perform_update(request, partial=True, method="PATCH", *args, **kwargs)

    def _perform_update(self, request, partial=False, method="UPDATE", *args, **kwargs):
        """
        Internal method to handle both full and partial updates with comprehensive logging.
        """
        instance = self.get_object()
        patient_identifier = instance.nhs_number or instance.unique_reference_number or f"ID {instance.id}"
        
        logger.info(f"🔄 {method} update attempt for patient {patient_identifier} by {request.user.email if request.user else 'unidentified user'}")
        
        # Verify the patient is in the accessible queryset
        if instance not in self.get_queryset():
            logger.warning(f"❌ {method} update denied - patient {patient_identifier} not in user's PDU scope")
            return self.create_npda_response(
                data={"detail": "You do not have permission to modify this patient record"},
                status=status.HTTP_403_FORBIDDEN,
                advisory_message="Access denied - patient not in your PDU scope",
                advisory_type='warning'
            )
        
        # Log the fields being updated (for audit purposes)
        updated_fields = list(request.data.keys()) if hasattr(request, 'data') else []
        logger.info(f"🔄 {method} updating fields: {updated_fields} for patient {patient_identifier}")
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            logger.warning(f"❌ {method} validation failed for patient {patient_identifier}: {serializer.errors}")
            return self.create_npda_response(
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
                advisory_message=f"Patient data validation failed for {method.lower()} update",
                advisory_type='warning'
            )
        
        try:
            with transaction.atomic():
                self.perform_update(serializer)
                
                # Log successful update
                logger.info(f"✅ {method} update successful for patient {patient_identifier}")
            
            # Create advisory message with helpful details
            field_count = len(updated_fields)
            advisory_message = f"Patient {patient_identifier} updated via {method}"
            if field_count > 0:
                advisory_message += f" ({field_count} field{'s' if field_count != 1 else ''} modified)"
            
            return self.create_npda_response(
                data=serializer.data,
                status=status.HTTP_200_OK,
                advisory_message=advisory_message,
                advisory_type='info'
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to {method} update patient {patient_identifier}: {str(e)}")
            return self.create_npda_response(
                data={"detail": f"Failed to {method.lower()} update patient record"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                advisory_message=f"{method} update operation failed - please try again",
                advisory_type='warning'
            )
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete operations are not supported for visits.
        Use the web interface for visit management.
        """
        return Response(
            {"detail": "Delete operations are not supported for patients. Use the web interface for visit management."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def get_serializer_context(self):
        """
        Provide context needed for form validation in the serializer.
        """
        context = super().get_serializer_context()
        
        # Add PDU context
        pdu = self.get_pdu_for_request()
        if pdu:
            context['paediatric_diabetes_unit'] = pdu
        
        # Add audit period context
        try:
            from project.npda.models import AuditPeriod
            active_audit_dates = get_audit_period_for_date(timezone.now())
            audit_period = AuditPeriod.objects.filter(
                start_date__year=active_audit_dates[0].year,
                end_date__year=active_audit_dates[1].year,
            ).first()
            
            if audit_period:
                context['audit_period'] = audit_period
            else:
                # Log the issue but don't fail the serializer context creation
                logger.warning("No active audit period found for serializer context")
                
        except Exception as e:
            logger.error(f"Error getting audit period for serializer context: {str(e)}")
        
        # Add override_postcode flag from request data
        if hasattr(self.request, 'data'):
            context['override_postcode'] = self.request.data.get('override_postcode', False)
        
        return context
    
    def get_object(self):
        """
        Override to lookup by NHS number or URN instead of primary key.
        Only searches within the user's accessible patients from active submissions.
        """
        queryset = self.get_queryset() # the queryset is already filtered by user's PDUs
        lookup_value = self.kwargs.get('pk')  # DRF still uses 'pk' in kwargs
        
        if not lookup_value:
            raise Http404("No patient identifier provided")
        # Try to find patient by NHS number first, then URN
        try:
            # URNs are only used in Jersey
            pdu = self.get_pdu_for_request()
            if pdu and pdu.pz_code == 'PZ248':  # Jersey PDU code
                patient = queryset.get(unique_reference_number=lookup_value)
            else:
                patient = queryset.get(nhs_number=lookup_value)
            
            return patient
            
        except Patient.DoesNotExist:
            logger.warning(f"❌ Patient not found for identifier: {lookup_value}")
            raise Http404(f"Patient with identifier '{lookup_value}' not found in your accessible patients")
        
        except Patient.MultipleObjectsReturned:
            logger.error(f"❌ Multiple patients found for identifier: {lookup_value}")
            raise Http404(f"Multiple patients found for identifier '{lookup_value}' - contact NPDA team for assistance")