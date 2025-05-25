from django.apps import apps
from django.db import transaction
from django.utils import timezone
import logging

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.http import Http404
from oauth2_provider.contrib.rest_framework import TokenHasScope, TokenHasReadWriteScope
from django_filters.rest_framework import DjangoFilterBackend

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
                pdu_codes = user.paediatric_diabetes_units.values_list('paediatric_diabetes_unit__pz_code', flat=True)
                paediatric_diabetes_units = PaediatricDiabetesUnit.objects.filter(pz_code__in=pdu_codes)
                transfers = Transfer.objects.filter(
                    paediatric_diabetes_unit__in=paediatric_diabetes_units,
                    date_leaving_service__isnull=True,
                    reason_leaving_service__isnull=True
                )
                queryset = queryset.filter(paediatric_diabetes_units__in=transfers)
            else:
                # User has no assigned PDUs - return empty queryset 
                queryset = queryset.none()
        
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
        Handle PUT requests for full patient record updates.
        All required fields must be provided.
        """
        logger.info(f"🔄 PUT request for patient update by user {request.user.id}")
        return self._perform_update(request, partial=False, method="PUT", *args, **kwargs)

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
        print("Being called _perform_update")
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
        Delete a patient record with PDU scope validation.
        """
        instance = self.get_object()
        
        # Verify the patient is in the accessible queryset
        if instance not in self.get_queryset():
            return self.create_npda_response(
                data={"detail": "You do not have permission to delete this patient record"},
                status=status.HTTP_403_FORBIDDEN,
                advisory_message="Access denied - patient not in your PDU scope",
                advisory_type='warning'
            )
        
        # Store patient identifier before deletion
        patient_identifier = instance.nhs_number or instance.unique_reference_number or f"ID {instance.id}"
        
        try:
            with transaction.atomic():
                self.perform_destroy(instance)
            
            # Success response for deletion
            return self.create_npda_response(
                data={"detail": "Patient record deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
                advisory_message=f"Patient {patient_identifier} permanently removed from system",
                advisory_type='warning'  # Use warning for deletion as it's irreversible
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to delete patient {patient_identifier}: {str(e)}")
            return self.create_npda_response(
                data={"detail": "Failed to delete patient record"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                advisory_message="Delete operation failed - please try again",
                advisory_type='warning'
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
            if pdu and pdu.pz_code == 'JER':
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