from django.db import models
from core.models.contact import Contact
from core.models.messagelog import MessageLogs

class ContactAnalytics(Contact):
    class Meta:
        proxy = True
        verbose_name = 'Contact Analytics'
        verbose_name_plural = 'Contact Analytics'

class MessageAnalytics(MessageLogs):
    class Meta:
        proxy = True
        verbose_name = 'Message Analytics'
        verbose_name_plural = 'Message Analytics'
    
class ContactAnalyticsForMedia(Contact):
    """
    Proxy model for Contact to provide media-specific analytics views
    """
    class Meta:
        proxy = True
        verbose_name = 'Contact Analytics for Media'
        verbose_name_plural = 'Contact Analytics for Media'
        
    def get_media_stats(self):
        """Get media-specific statistics for this contact"""
        return {
            'is_lead': self.is_lead,
            'is_appointment': self.is_appointment,
            'total_revenue': self.bill_charge_total_history or 0,
            'relationship_tag': self.relationship_tag
        }

# Show two tables:
    # 1. Relationship Tag == "Botox" with the following columns:
    #    - Total Contacts
    #    - Total Leads (is_lead)
    #    - Total Appointments (is_appointment)
    #    - Total Revenue (bill_charge_total_history)
    #    - Show ONLY current month, but possibility to filter by month to see others. Filter by 'store' and 'region' too
    #    - rows created_at so we can see daily evolution 

    # 2. Relationship Tag == "Preenchimento" with the following columns:
    #    - Total Contacts
    #    - Total Leads (is_lead)
    #    - Total Appointments (is_appointment)
    #    - Total Revenue (bill_charge_total_history)
    #    - Show ONLY current month, but possibility to filter by month to see others. Filter by 'store' and 'region' too
    #    - rows created_at so we can see daily evolution