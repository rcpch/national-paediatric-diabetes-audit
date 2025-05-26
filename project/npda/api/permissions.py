from oauth2_provider.contrib.rest_framework import TokenHasScope
import logging

logger = logging.getLogger(__name__)

class TokenHasPatientScopeAndPDUAccess(TokenHasScope):
    """
    Permission class that enforces:
    1. OAuth scope validation (patient:read for GET/LIST, patient:write for POST/PUT/PATCH)
    2. PDU access control (tokens scoped to specific PDUs)
    3. Admin bypass (admin:cross-pdu scope allows access to all PDUs)

    NOTE : Still some validation occuring in the viewset, this is just a permission class
    """
    
    
    def has_object_permission(self, request, view, obj):
        """
        Check object-level permissions for PDU scoping.
        Admin tokens with admin:cross-pdu bypass this check.
        """
        # Check if token has PDU profile
        if not hasattr(request.auth, 'pdu_profile') or not request.auth.pdu_profile:
            return False
        
        pdu_profile = request.auth.pdu_profile
        
        # Check for admin:cross-pdu scope
        token_scopes = request.auth.scope.split() if hasattr(request.auth, 'scope') else []
        is_admin_cross_pdu = 'admin:cross-pdu' in token_scopes
        
        if is_admin_cross_pdu:
            logger.info(f"✅ Admin cross-PDU access: bypassing PDU scoping for object")
            return True
        
        # For non-admin tokens, check PDU access
        if hasattr(obj, 'paediatric_diabetes_unit'):
            # Direct PDU relationship (like Patient model)
            object_pdu = obj.paediatric_diabetes_unit
            token_pdu = pdu_profile.paediatric_diabetes_unit
            
            if object_pdu == token_pdu:
                logger.debug(f"✅ PDU access granted: object in token's PDU {token_pdu.pz_code}")
                return True
            else:
                logger.warning(f"❌ PDU access denied: object in {object_pdu.pz_code if object_pdu else 'no PDU'}, token for {token_pdu.pz_code}")
                return False
        
        elif hasattr(obj, 'patient') and hasattr(obj.patient, 'paediatric_diabetes_unit'):
            # Indirect PDU relationship (like Visit model through patient)
            patient_pdu = obj.patient.paediatric_diabetes_unit
            token_pdu = pdu_profile.paediatric_diabetes_unit

            
            if patient_pdu == token_pdu:
                logger.debug(f"✅ PDU access granted: patient in token's PDU {token_pdu.pz_code}")
                return True
            else:
                logger.warning(f"❌ PDU access denied: patient in {patient_pdu.pz_code if patient_pdu else 'no PDU'}, token for {token_pdu.pz_code}")
                return False
        
        # If object doesn't have PDU context, deny access by default
        logger.warning(f"❌ No PDU context found for object type: {type(obj)}")
        return False