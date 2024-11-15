# apiSocialHub/models/file_message.py
from django.db import models

class FileMessage(models.Model):
    phone = models.CharField(max_length=15)
    message = models.TextField()
    file = models.FileField(upload_to='uploads/')
    status = models.CharField(max_length=50, blank=True, null=True)
    response = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"File Message to {self.phone}"