from django.db import models
from core.models.user import kUser
from django.utils import timezone
from apiCrm.models.lead import Lead

class Contact(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now)
    relationship_tag = models.CharField(max_length=100, null=True, blank=True, default='')
    source = models.CharField(max_length=100, null=True, blank=True, default="Whatsapp")
    store = models.CharField(max_length=100, null=True, blank=True, default="CENTRAL")
    region = models.CharField(max_length=100, null=True, blank=True, default="São Paulo")
    user = models.ForeignKey(kUser, on_delete=models.CASCADE)
    
    # External Info - CRM / Social Hub
    reference_code = models.CharField(max_length=100, null=True, blank=True)
    external_tag = models.CharField(max_length=255, null=True, blank=True, default="SEM TAGS")  # Map to 'Tags' column
    tag = models.CharField(max_length=255, null=True, blank=True)  # Internal tag (e.g., 'botox')
    status = models.CharField(max_length=255, null=True, blank=True, default="landing page")  # Default value

    # Lead tracking fields
    is_lead = models.BooleanField(default=False)
    lead_id = models.CharField(max_length=100, null=True, blank=True)
    lead_status = models.CharField(max_length=100, null=True, blank=True)
    lead_created_at = models.DateTimeField(null=True, blank=True)
    lead_last_checked = models.DateTimeField(null=True, blank=True)
    lead_check_count = models.IntegerField(default=0)

    def __str__(self):
        lead_info = f" (Lead: {self.lead_status})" if self.is_lead else ""
        return f"{self.name} - {self.phone}{lead_info}"

    def check_if_lead_exists(self):
        """
        Check if this contact exists as a lead in the CRM.
        Returns the Lead object if found, None otherwise.
        Updates contact's lead status fields.
        """
        # Update check tracking
        self.lead_last_checked = timezone.now()
        self.lead_check_count += 1
        self.save()

        # Clean phone number to match CRM format (keep only digits)
        clean_phone = ''.join(filter(str.isdigit, self.phone))
        clean_phone = clean_phone[-11:] if len(clean_phone) > 11 else clean_phone  # Handle country code
        
        try:
            # Try to find a matching lead by phone number (clean both sides for comparison)
            leads = Lead.objects.all()
            for lead in leads:
                lead_clean_phone = ''.join(filter(str.isdigit, lead.phone))
                lead_clean_phone = lead_clean_phone[-11:] if len(lead_clean_phone) > 11 else lead_clean_phone
                if clean_phone == lead_clean_phone:
                    self._update_lead_status(lead)
                    return lead
            
            # If no phone match and phone is empty or invalid, try by name
            if not clean_phone or len(clean_phone) < 8:  # Phone is empty or too short
                lead = Lead.objects.filter(name__iexact=self.name).first()
                if lead:
                    self._update_lead_status(lead)
                    return lead
            
            # If no lead is found, clear the status
            self._clear_lead_status()
            return None
            
        except Lead.DoesNotExist:
            self._clear_lead_status()
            return None

    def needs_lead_check(self, hours=24):
        """
        Check if this contact needs to be checked for lead status.
        Returns True if the contact hasn't been checked in the specified hours
        or has never been checked.
        """
        if not self.lead_last_checked:
            return True
        
        time_since_check = timezone.now() - self.lead_last_checked
        return time_since_check.total_seconds() > hours * 3600

    def get_lead_check_stats(self):
        """
        Get statistics about lead checks for this contact.
        """
        return {
            'total_checks': self.lead_check_count,
            'last_checked': self.lead_last_checked,
            'is_lead': self.is_lead,
            'lead_status': self.lead_status,
            'lead_age': (timezone.now() - self.lead_created_at).days if self.lead_created_at else None
        }

    def _update_lead_status(self, lead):
        """Update contact's lead status fields based on the found lead."""
        self.is_lead = True
        self.lead_id = lead.id_crm
        self.lead_status = lead.status
        self.lead_created_at = lead.created_at
        self.save()

    def _clear_lead_status(self):
        """Clear lead status fields when no lead is found."""
        self.is_lead = False
        self.lead_id = None
        self.lead_status = None
        self.lead_created_at = None
        self.save()