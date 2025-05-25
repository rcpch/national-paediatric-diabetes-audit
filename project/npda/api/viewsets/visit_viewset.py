from django.apps import apps
from django.db import transaction
from django.utils import timezone
import logging

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.http import Http404
from oauth2_provider.contrib.rest_framework import TokenHasScope, TokenHasReadWriteScope
from django_filters.rest_framework import DjangoFilterBackend

from project.npda.models import Visit, Patient, AuditPeriod, Transfer, Submission, NPDAUser, PaediatricDiabetesUnit
from project.npda.api.serializers.visit_serializer import VisitSerializer
from project.npda.general_functions import get_audit_period_for_date
from project.npda.api.response_metadata import NPDAResponseMixin

logger = logging.getLogger(__name__)

class VisitViewSet(NPDAResponseMixin, viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Visit instances nested under patients.
    
    This ViewSet provides CRUD operations for Visit records that belong to specific patients.
    All visits are accessed via /patients/{patient_id}/visits/ endpoints.
    Validation is handled by the VisitSerializer which delegates to VisitForm.
    The queryset is filtered based on the user's permissions and PDU access.

    Requires OAuth2 authentication with appropriate scopes:
    - GET: 'patient:read' scope
    - POST/PUT/PATCH: 'patient:write' scope
    
    For OAuth2 tokens with PDU profiles, data is automatically scoped to the token's PDU.
    Visits are only accessible for patients within the user's assigned PDUs.
    """
    serializer_class = VisitSerializer
    filter_backends = [DjangoFilterBackend]
    
    # Allow read and write operations, but no delete
    http_method_names = ['get', 'post', 'put', 'patch', 'options', 'head']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        Since visits are nested under patients, we inherit the same permission model.
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

    def get_patient(self):
        """
        Get the patient from the URL parameters and verify access.
        This method handles all the PDU scoping validation.
        """
        patient_pk = self.kwargs.get('patient_pk')
        if not patient_pk:
            raise Http404("No patient identifier provided")
        
        # Get PDU for scoping
        pdu = self.get_pdu_for_request()
        
        try:
            # Find patient with PDU scoping
            if pdu and pdu.pz_code == 'PZ248':  # Jersey PDU code
                patient = Patient.objects.get(unique_reference_number=patient_pk)
            else:
                patient = Patient.objects.get(nhs_number=patient_pk)
            
            # Verify patient is in accessible PDU - this is the key security check
            if pdu:
                patient_pdus = Transfer.objects.filter(
                    patient=patient,
                    date_leaving_service__isnull=True,
                    reason_leaving_service__isnull=True
                ).values_list('paediatric_diabetes_unit', flat=True)
                
                if pdu.pk not in patient_pdus:
                    raise Http404("Patient not accessible within your PDU scope")
            
            return patient
            
        except Patient.DoesNotExist:
            logger.warning(f"❌ Patient not found for identifier: {patient_pk}")
            raise Http404(f"Patient with identifier '{patient_pk}' not found")
        
        except Patient.MultipleObjectsReturned:
            logger.error(f"❌ Multiple patients found for identifier: {patient_pk}")
            raise Http404(f"Multiple patients found for identifier '{patient_pk}'")

    def get_queryset(self):
        """
        Filter visits to only those belonging to the specified patient.
        Since get_patient() already validates PDU access, we can trust this is secure.
        """
        patient = self.get_patient()  # This call validates PDU access
        
        # Return visits for this specific patient, ordered by date
        queryset = Visit.objects.filter(
            patient=patient
        ).select_related('patient').order_by('-visit_date', '-id')
        
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
        
        return None
    
    def list(self, request, *args, **kwargs):
        """
        Return a list of visits for the specified patient.
        """
        patient = self.get_patient()
        queryset = self.filter_queryset(self.get_queryset())
        
        # Log the request for audit purposes
        patient_identifier = patient.nhs_number or patient.unique_reference_number or f"ID {patient.id}"
        pdu = self.get_pdu_for_request()
        pdu_info = f" for PDU {pdu.pz_code}" if pdu else ""
        logger.info(f"📋 Visit list requested for patient {patient_identifier} by {request.user.email}{pdu_info}")
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data)
            
            # Add metadata to paginated response
            if hasattr(response_data, 'data'):
                return self.create_npda_response(
                    data=response_data.data,
                    status=status.HTTP_200_OK,
                    advisory_message=f"Retrieved {len(page)} visits for patient {patient_identifier} from {queryset.count()} total{pdu_info}",
                    advisory_type='info'
                )
            return response_data
        
        serializer = self.get_serializer(queryset, many=True)
        return self.create_npda_response(
            data=serializer.data,
            status=status.HTTP_200_OK,
            advisory_message=f"Retrieved {len(serializer.data)} visits for patient {patient_identifier}{pdu_info}",
            advisory_type='info'
        )
    
    def retrieve(self, request, *args, **kwargs):
        """
        Return a specific visit for the specified patient.
        """
        patient = self.get_patient()
        instance = self.get_object()
        patient_identifier = patient.nhs_number or patient.unique_reference_number or f"ID {patient.id}"
        
        logger.info(f"🔍 Visit {instance.id} retrieved for patient {patient_identifier} by {request.user.email}")
        
        serializer = self.get_serializer(instance)
        return self.create_npda_response(
            data=serializer.data,
            status=status.HTTP_200_OK,
            advisory_message=f"Visit {instance.id} details for patient {patient_identifier}",
            advisory_type='info'
        )
    
    def create(self, request, *args, **kwargs):
        """
        Create a new visit record for the specified patient.
        The patient identifier from the URL is automatically used.
        """
        patient = self.get_patient()  # This validates PDU access
        
        # No need to re-validate PDU since get_patient() already did it
        pdu = self.get_pdu_for_request()
        if not pdu:
            return Response(
                {"detail": "No PDU context available for this request"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        patient_identifier = patient.nhs_number or patient.unique_reference_number or f"ID {patient.id}"
        logger.info(f"📝 Creating visit for patient {patient_identifier} in PDU {pdu.pz_code} by user {request.user.email}")
        
        # Add patient identifier to request data automatically
        request_data = request.data.copy()
        if patient.nhs_number:
            request_data['patient_nhs_number'] = patient.nhs_number
        elif patient.unique_reference_number:
            request_data['patient_unique_reference_number'] = patient.unique_reference_number
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            serializer = self.get_serializer(data=request_data)
            if serializer.is_valid(raise_exception=True):
                self.perform_create(serializer)
                
                logger.info(f"✅ Visit created successfully for patient {patient_identifier}")
                
                return self.create_npda_response(
                    data=serializer.data,
                    status=status.HTTP_201_CREATED,
                    advisory_message=f"Visit created for patient {patient_identifier}",
                    advisory_type='info'
                )
            else:
                return Response(
                    serializer.errors, 
                    status=status.HTTP_400_BAD_REQUEST
                )

    def perform_create(self, serializer):
        """
        Save the visit record with all required validations.
        The VisitForm handles all business logic validation and external validators.
        """
        paediatric_diabetes_unit = self.get_pdu_for_request()
        
        if not paediatric_diabetes_unit:
            raise ValueError("No PDU context available for visit creation")
        
        try:
            visit = serializer.save()
            
            # Log successful creation with patient context
            patient_identifier = visit.patient.nhs_number or visit.patient.unique_reference_number or f"ID {visit.patient.id}"
            logger.info(f"✅ Visit {visit.id} successfully created for patient {patient_identifier} "
                       f"via OAuth2 for PDU {paediatric_diabetes_unit.pz_code}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create visit: {str(e)}")
            raise ValueError(f"Failed to create visit record: {str(e)}")
    
    def update(self, request, *args, **kwargs):
        """
        Handle PUT requests for full visit record updates.
        """
        patient = self.get_patient()
        patient_identifier = patient.nhs_number or patient.unique_reference_number or f"ID {patient.id}"
        logger.info(f"🔄 PUT request for visit update for patient {patient_identifier} by user {request.user.email}")
        return self._perform_update(request, partial=False, method="PUT", *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        Handle PATCH requests for partial visit record updates.
        """
        patient = self.get_patient()
        patient_identifier = patient.nhs_number or patient.unique_reference_number or f"ID {patient.id}"
        logger.info(f"🔄 PATCH request for visit update for patient {patient_identifier} by user {request.user.email}")
        return self._perform_update(request, partial=True, method="PATCH", *args, **kwargs)

    def _perform_update(self, request, partial=False, method="UPDATE", *args, **kwargs):
        """
        Internal method to handle both full and partial updates with comprehensive logging.
        """
        patient = self.get_patient()
        instance = self.get_object()
        patient_identifier = patient.nhs_number or patient.unique_reference_number or f"ID {patient.id}"
        
        logger.info(f"🔄 {method} update attempt for visit {instance.id} (patient {patient_identifier}) by {request.user.email}")
        
        # Log the fields being updated (for audit purposes)
        updated_fields = list(request.data.keys()) if hasattr(request, 'data') else []
        logger.info(f"🔄 {method} updating fields: {updated_fields} for visit {instance.id}")
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            logger.warning(f"❌ {method} validation failed for visit {instance.id}: {serializer.errors}")
            return self.create_npda_response(
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
                advisory_message=f"Visit data validation failed for {method.lower()} update",
                advisory_type='warning'
            )
        
        try:
            with transaction.atomic():
                self.perform_update(serializer)
                
                # Log successful update
                logger.info(f"✅ {method} update successful for visit {instance.id} (patient {patient_identifier})")
            
            # Create advisory message with helpful details
            field_count = len(updated_fields)
            advisory_message = f"Visit for patient {patient_identifier} updated via {method}"
            if field_count > 0:
                advisory_message += f" ({field_count} field{'s' if field_count != 1 else ''} modified)"
            
            return self.create_npda_response(
                data=serializer.data,
                status=status.HTTP_200_OK,
                advisory_message=advisory_message,
                advisory_type='info'
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to {method} update visit {instance.id}: {str(e)}")
            return self.create_npda_response(
                data={"detail": f"Failed to {method.lower()} update visit record"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                advisory_message=f"{method} update operation failed - please try again",
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
        
        return context
    
    def get_object(self):
        """
        Override to lookup visit by ID within the patient's visits.
        """
        queryset = self.get_queryset()  # Already filtered to patient's visits
        lookup_value = self.kwargs.get('pk')  # Visit ID
        
        if not lookup_value:
            raise Http404("No visit identifier provided")
        
        try:
            visit = queryset.get(id=lookup_value)
            return visit
            
        except Visit.DoesNotExist:
            patient = self.get_patient()
            patient_identifier = patient.nhs_number or patient.unique_reference_number or f"ID {patient.id}"
            logger.warning(f"❌ Visit not found for ID: {lookup_value} for patient {patient_identifier}")
            raise Http404(f"Visit with ID '{lookup_value}' not found for patient {patient_identifier}")
        
        except Visit.MultipleObjectsReturned:
            logger.error(f"❌ Multiple visits found for ID: {lookup_value}")
            raise Http404(f"Multiple visits found for ID '{lookup_value}' - this should not happen")
    
    # DESTRUCTIVE ACTIONS ARE DISABLED
    def destroy(self, request, *args, **kwargs):
        """
        Delete operations are not supported for visits.
        Use the web interface for visit management.
        """
        return Response(
            {"detail": "Delete operations are not supported for visits. Use the web interface for visit management."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )