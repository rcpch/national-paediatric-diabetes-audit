from rest_framework import permissions
from oauth2_provider.contrib.rest_framework import TokenHasScope

class TokenHasPatientScopeAndPDUAccess(TokenHasScope):
    """
    Permission class that combines OAuth token scope validation with PDU access control.
    Requires the token to have the appropriate scope and the user to have access to the patient's PDU.
    """
    
    def has_object_permission(self, request, view, obj):
        # First check if token has correct scope
        has_scope = super().has_permission(request, view)
        if not has_scope:
            return False
        
        user = request.user
        
        # Superusers and RCPCH staff/audit team have full access
        if user.is_superuser or user.is_rcpch_audit_team_member or user.is_rcpch_staff:
            return True
        
        # If we're accessing a patient object, check PDU access
        if hasattr(obj, 'paediatric_diabetes_unit'):
            # Get PDU codes this user has access to
            user_pdu_codes = user.paediatric_diabetes_units.values_list('pz_code', flat=True)
            patient_pdu_code = obj.paediatric_diabetes_unit.pz_code if obj.paediatric_diabetes_unit else None
            
            # Allow access if patient's PDU is in user's accessible PDUs
            return patient_pdu_code in user_pdu_codes
        
        # Deny access by default
        return False