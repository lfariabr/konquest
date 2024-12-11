from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import EmailValidator

class kUser(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    company = models.CharField(max_length=100, null=True, blank=True)
    password = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.name
    
    class Meta:
        indexes = [models.Index(fields=['id'])]