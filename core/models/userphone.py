from django.db import models
from core.models.user import User

class UserPhone(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)
    phone_token = models.CharField(max_length=100)
    phone_description = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)