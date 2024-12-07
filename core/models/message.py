from django.db import models
from core.models.user import kUser
from core.models.filetype import FileType
from django.utils import timezone

class Message(models.Model):
    user = models.ForeignKey(kUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    text = models.TextField()
    counter = models.IntegerField(default=0)
    file = models.FileField(null=True, blank=True)
    file_type = models.CharField(max_length=20, choices=FileType.choices, null=True, blank=True)
    relationship_tag = models.CharField(max_length=100, null=True, blank=True, default='')
    contact_type = models.CharField(max_length=100, null=True, blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)

    def should_create_lead(self):
        pass