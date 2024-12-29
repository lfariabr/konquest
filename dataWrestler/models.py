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