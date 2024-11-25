from django.db import models
from django.utils import timezone
from core.models.contact import Contact
from core.models.message import Message
from core.models.userphone import UserPhone
from messageShooter.models.target_list import TargetList

QUEUE_STATUS = [
    'pending',    # Initial state
    'processing', # Being processed
    'sent',       # Successfully sent
    'failed',     # Failed to send
    'retrying'    # Failed but will retry
]

class Queue(models.Model):
    """
    Queue for messages to be sent
    """
    # Contacts to receive message
    target_list = models.ForeignKey(TargetList, on_delete=models.CASCADE) # I want to be able to ACCESS each target list
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE) # do we really need this?
    
    # Payload completion
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    userphone = models.ForeignKey(UserPhone, on_delete=models.CASCADE)
    phone_token = models.CharField(max_length=255)
    
    # Processing
    status = models.CharField(max_length=20, choices=[(s, s) for s in QUEUE_STATUS], default='pending')
    priority = models.IntegerField(default=1)  # Higher number = higher priority
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    retry_count = models.IntegerField(default=0)
    last_error = models.TextField(null=True, blank=True)
    scheduled_time = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-priority', 'scheduled_time', 'created_at']  # Process higher priority first, then by schedule, then FIFO

    def __str__(self):
        return f"Queue item {self.id} for target list {self.target_list.id}"