from django.db import models
from django.utils import timezone
from core.models.contact import Contact
from core.models.message import Message
from core.models.userphone import UserPhone
from messageShooter.models.target_list import TargetList
from messageShooter.models.campaign import Campaign

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
    # Target list to process
    target_list = models.ForeignKey(TargetList, on_delete=models.CASCADE)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, null=True)
    
    # Message and sender information
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    userphone = models.ForeignKey(UserPhone, on_delete=models.CASCADE)
    phone_token = models.CharField(max_length=255)
    
    # Processing
    status = models.CharField(max_length=100, choices=[(s, s) for s in QUEUE_STATUS], default='pending')
    priority = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    retry_count = models.IntegerField(default=0)
    last_error = models.TextField(null=True, blank=True)
    scheduled_time = models.DateTimeField(default=timezone.now)
    processed_contacts = models.JSONField(default=dict, help_text='Tracks status of each contact in the target list')
    total_contacts = models.IntegerField(default=0, help_text='Total number of contacts to process')
    processed_count = models.IntegerField(default=0, help_text='Number of contacts processed')

    class Meta:
        ordering = ['-priority', 'scheduled_time', 'created_at']

    def __str__(self):
        return f"Queue item {self.id} for target list {self.target_list.id} ({self.processed_count}/{self.total_contacts} processed)"

    def get_progress(self):
        """Returns the progress percentage of processed contacts"""
        if self.total_contacts == 0:
            return 0
        return (self.processed_count / self.total_contacts) * 100