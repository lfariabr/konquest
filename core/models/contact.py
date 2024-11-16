from django.db import models

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
    external_tag = models.CharField(max_length=255, null=True, blank=True, default="SEM TAGS")  # Map to 'Tags' column
    tag = models.CharField(max_length=255, null=True, blank=True)  # Internal tag (e.g., 'botox')
    status = models.CharField(max_length=255, null=True, blank=True, default="landing page")  # Default value

    def __str__(self):
        return f"{self.name} - {self.phone}"