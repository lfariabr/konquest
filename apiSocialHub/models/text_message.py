# apiSocialHub/models/text_message.py
from django.db import models

class TextMessage(models.Model):
    phone = models.CharField(max_length=15)
    message = models.TextField()
    status = models.CharField(max_length=50, blank=True, null=True)
    response = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Text Message to {self.phone}"