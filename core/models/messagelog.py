from django.db import models
from core.models.user import kUser
from core.models.contact import Contact
from core.models.message import Message
from core.models.userphone import UserPhone

class MessageLogs(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    user = models.ForeignKey(kUser, on_delete=models.CASCADE)
    user_phone = models.ForeignKey(UserPhone, on_delete=models.CASCADE, null=True, blank=True)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=100)
    sent_at = models.DateTimeField(auto_now_add=True) # Change this to import message logs maybe
    relationship_tag = models.CharField(max_length=100, null=True, blank=True, default='')

    class Meta:
        verbose_name = 'Message Log'
        verbose_name_plural = 'Message Logs'