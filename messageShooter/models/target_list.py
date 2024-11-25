# priority 

# contact phone
# contact_type
# contact_tag
# reference_id = {
#   (if whatsapp, core>models>contact>id),
#   (if appointment, apiCrm>models>appointment>id_crm)
#   (if lead, apiCrm>models>lead),
#}

# sent_messages_count

# userphone token

from django.db import models
from core.models.userphone import UserPhone
from core.models.message import Message
from core.models.contact import Contact
from django.utils import timezone

class TargetList(models.Model):
    # Contact information
    contact = models.ForeignKey('core.Contact', on_delete=models.CASCADE, null=True)
    contact_phone = models.CharField(max_length=20)
    contact_type = models.CharField(max_length=100)
    contact_tag = models.CharField(max_length=100)
    reference_id = models.CharField(max_length=100)

    # Message tracking
    sent_messages_count = models.IntegerField(default=0)
    message = models.ForeignKey('core.Message', on_delete=models.CASCADE)
    userphone = models.ForeignKey('core.UserPhone', on_delete=models.CASCADE)
    token = models.CharField(max_length=100, null=True, blank=True)  # Making token nullable

    # Processing
    status = models.CharField(max_length=100, default='pending')  # pending, processing, completed, failed
    priority = models.IntegerField(default=0)  # Default 0 for FIFO
    sequence_order = models.IntegerField(default=0, help_text="Order in the campaign sequence")
    days_interval = models.IntegerField(null=True, blank=True, help_text="Days to wait before sending (for appointment campaigns)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priority', 'sequence_order', 'created_at']  # FIFO ordering
        indexes = [
            models.Index(fields=['contact_type', 'contact_tag']),
            models.Index(fields=['status', 'priority', 'sequence_order']),
        ]

    def __str__(self):
        return f"{self.contact_type}:{self.contact_tag} - {self.contact_phone}"
