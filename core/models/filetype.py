from django.db import models

class FileType(models.TextChoices):
    IMAGE = 'image'
    VIDEO = 'video'
    AUDIO = 'audio'