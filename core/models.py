from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Contact(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    relationship_tag = models.CharField(max_length=100, null=True, blank=True, default='')
    source = models.CharField(max_length=100, null=True, blank=True, default="Whatsapp")
    store = models.CharField(max_length=100, null=True, blank=True, default="CENTRAL")
    region = models.CharField(max_length=100, null=True, blank=True, default="São Paulo")
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    
    # External Info - CRM / Social Hub
    reference_code = models.CharField(max_length=100, null=True, blank=True)
    external_tag = models.CharField(max_length=100, null=True, blank=True, default="SEM TAGS")
    
class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    company = models.CharField(max_length=100, null=True, blank=True)
    password = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
class UserPhone(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)
    phone_token = models.CharField(max_length=100)
    phone_description = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

class FileType(models.TextChoices):
    IMAGE = 'image'
    VIDEO = 'video'
    AUDIO = 'audio'

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    text = models.TextField()
    counter = models.IntegerField(default=0)
    file = models.FileField(null=True, blank=True)
    file_type = models.CharField(max_length=20, choices=FileType.choices, null=True, blank=True)

class MessageLogs(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_phone = models.ForeignKey(UserPhone, on_delete=models.CASCADE, null=True, blank=True)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=100)
    sent_at = models.DateTimeField(auto_now_add=True)
    