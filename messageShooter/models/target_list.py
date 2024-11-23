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
from django.utils import timezone

class TargetList(models.Model):
    # Contact information
    contact_phone = models.CharField(max_length=20)
    contact_type = models.CharField(max_length=100)
    contact_tag = models.CharField(max_length=100)
    reference_id = models.CharField(max_length=100)

    # Message tracking
    sent_messages_count = models.IntegerField(default=0)
    userphone = models.ForeignKey(UserPhone, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)

    # Processing
    priority = models.IntegerField(default=0)  # Default 0 for FIFO
    status = models.CharField(max_length=50, default='pending')  # pending, processing, completed, failed
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priority', 'created_at']  # FIFO ordering

    def __str__(self):
        return f"{self.contact_type}:{self.contact_tag} - {self.contact_phone}"
