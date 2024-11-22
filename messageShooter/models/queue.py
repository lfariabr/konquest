from django.db import models
from messageShooter.models.target_list import TargetList

QUEUE_STATUS = [
    'pending',    # Initial state
    'processing', # Being processed
    'completed',  # Successfully sent
    'failed',     # Failed to send
    'retrying'    # Failed but will retry
]

class Queue(models.Model):
    target_list = models.ForeignKey(TargetList, on_delete=models.CASCADE)
    priority = models.IntegerField(default=1)  # Higher number = higher priority
    status = models.CharField(max_length=20, choices=[(s, s) for s in QUEUE_STATUS], default='pending')
    scheduled_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    retry_count = models.IntegerField(default=0)
    last_error = models.TextField(null=True, blank=True)
    token = models.CharField(max_length=255)  # Token for message sending

    class Meta:
        ordering = ['-priority', 'scheduled_time', 'created_at']  # Process higher priority first, then by schedule, then FIFO

    def __str__(self):
        return f"Queue {self.id} - {self.target_list.contact_phone} ({self.status})"