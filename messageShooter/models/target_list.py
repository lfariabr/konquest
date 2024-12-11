# priority 

# contact phone
# contact_type
# contact_tag
# reference_id = {
#   (if whatsapp, core>models>contact>id),
#   (if appointment, apiCrm>models>appointment>id_crm)
#   (if lead, apiCrm>models>lead),
#}

# sent_messages_count

# userphone token

from django.core.exceptions import ValidationError
from django.db import models
from core.models.userphone import UserPhone
from core.models.message import Message
from core.models.contact import Contact
from messageShooter.models.campaign import Campaign
from django.utils import timezone
from django.core import validators

class TargetList(models.Model):
    CONTACT_TYPE_CHOICES = [
        ('Whatsapp', 'Whatsapp'),
        ('Appointment', 'Appointment')
    ]

    # Contact information
    contact = models.ForeignKey('core.Contact', on_delete=models.CASCADE, null=False)
    contact_phone = models.CharField(max_length=20, null=False, blank=False)
    contact_type = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        choices=CONTACT_TYPE_CHOICES,
        validators=[
            validators.RegexValidator(
                regex='^(Whatsapp|Appointment)$',
                message='Contact type must be either Whatsapp or Appointment',
                code='invalid_contact_type'
            )
        ]
    )
    contact_tag = models.CharField(max_length=100, null=False, blank=False)
    reference_id = models.CharField(max_length=100, null=True, blank=True)  # Making reference_id nullable

    # Message tracking
    sent_messages_count = models.IntegerField(default=0)
    message = models.ForeignKey('core.Message', on_delete=models.CASCADE, null=False)
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True, related_name='target_lists')
    userphone = models.ForeignKey('core.UserPhone', on_delete=models.CASCADE, null=False)
    token = models.CharField(max_length=100, null=True, blank=True)  # Making token nullable

    # Processing
    status = models.CharField(max_length=100, default='pending')  # pending, processing, completed, failed
    priority = models.IntegerField(default=0)  # Default 0 for FIFO
    sequence_order = models.IntegerField(default=0, help_text="Order in the campaign sequence")
    days_interval = models.IntegerField(null=True, blank=True, help_text="Days to wait before sending (for appointment campaigns)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate model fields"""
        super().clean()
        if self.contact_type not in dict(self.CONTACT_TYPE_CHOICES):
            raise ValidationError({
                'contact_type': 'Contact type must be either Whatsapp or Appointment'
            })

    def save(self, *args, **kwargs):
        """Override save to enforce validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    def get_contacts(self):
        """
        Get contacts associated with this target list using the appropriate resolver
        based on contact_type.
        """
        from messageShooter.resolvers.get_contacts import get_contact_whatsapp, get_contact_appointment

        if self.contact_type == 'Whatsapp':
            return get_contact_whatsapp(self.contact_type, self.contact_tag)
        elif self.contact_type == 'Appointment':
            return get_contact_appointment(self.contact_type, self.contact_tag)
        return []

    class Meta:
        ordering = ['priority', 'sequence_order', 'created_at']  # FIFO ordering
        indexes = [
            models.Index(fields=['contact_type', 'contact_tag']),
            models.Index(fields=['status', 'priority', 'sequence_order']),
        ]
        

    def __str__(self):
        return f"Target List {self.id} - {self.contact_tag}"
