from django.db import models
from core.models.user import User
from core.models.filetype import FileType

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    text = models.TextField()
    counter = models.IntegerField(default=0)
    file = models.FileField(null=True, blank=True)
    file_type = models.CharField(max_length=20, choices=FileType.choices, null=True, blank=True)