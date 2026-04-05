import re
from typing import Dict, Any

class SanitizationService:
    """
    HIPAA/Privacy Layer.
    Removes Personally Identifiable Information (PII) before sending data to LLMs.
    """

    def sanitize_encounter(self, encounter_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes raw encounter data and returns a version safe for external LLMs.
        """
        # 1. Remove obvious PII fields
        phi_fields = ["patient_id", "first_name", "last_name", "document_id", "phone", "email", "address"]
        
        sanitized = {k: v for k, v in encounter_data.items() if k not in phi_fields}
        
        # 2. Anonymize ID
        if "id" in sanitized:
            sanitized["id"] = "ANONYMIZED_ENCOUNTER"

        # 3. Fuzzy text scrubbing (Regex for emails and phones in notes)
        if "clinical_notes" in sanitized and sanitized["clinical_notes"]:
            text = sanitized["clinical_notes"]
            text = re.sub(r'\S+@\S+', '[EMAIL]', text) # Scruby emails
            text = re.sub(r'\+?\d{10,15}', '[PHONE]', text) # Scruby phones
            sanitized["clinical_notes"] = text

        return sanitized

# Singleton
sanitization_service = SanitizationService()
