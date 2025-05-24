import uuid
from django.utils import timezone
from django.conf import settings
from rest_framework.response import Response


class NPDAResponseMixin:
    """Mixin to provide consistent response headers for NPDA API viewsets."""

    def create_npda_response(self, data, status=200, advisory_message=None, advisory_type='info'):
        """
        Create a standardized NPDA response with metadata in headers.
        
        Args:
            data: Standard Django response data
            status: HTTP status code
            advisory_message: Optional advisory message string
            advisory_type: Advisory type ('info' or 'warning')
        
        Returns:
            Response: Standard DRF Response with NPDA headers
        """
        response = Response(data, status=status)
        
        # Add standard NPDA headers
        response['X-NPDA-Timestamp'] = timezone.now().isoformat()
        response['X-NPDA-Version'] = getattr(settings, 'API_VERSION', '1.0')
        response['X-Request-ID'] = str(uuid.uuid4())
        
        # Add advisory headers if provided
        if advisory_message:
            response['X-NPDA-Advisory'] = advisory_message
            response['X-NPDA-Advisory-Type'] = advisory_type
        
        return response

    def create_advisory_response(self, data, status=200, message='', advisory_type='info'):
        """
        Convenience method for responses with advisory messages.
        
        Args:
            data: Standard Django response data
            status: HTTP status code
            message: Advisory message string
            advisory_type: Advisory type ('info' or 'warning')
        """
        return self.create_npda_response(
            data=data,
            status=status,
            advisory_message=message,
            advisory_type=advisory_type
        )