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
from django.core.cache import cache

class TargetList(models.Model):
    CONTACT_TYPE_CHOICES = [
        ('Whatsapp', 'Whatsapp'),
        ('Appointment', 'Appointment')
    ]

    # Contact information
    contact = models.ForeignKey('core.Contact', on_delete=models.CASCADE, null=True, blank=True)  # Make nullable and blank-able
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

    # Cache settings
    CACHE_TIMEOUT = 3600  # 1 hour

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

    @classmethod
    def get_cached_target_lists(cls, user_id, contact_type=None, contact_tag=None):
        """Get cached target lists for a user"""
        cache_key = f'target_lists_{user_id}_{contact_type}_{contact_tag}'
        cached_lists = cache.get(cache_key)
        
        if cached_lists is not None:
            return cached_lists
            
        # Build query
        query = cls.objects.filter(userphone__user_id=user_id)
        if contact_type:
            query = query.filter(contact_type=contact_type)
        if contact_tag:
            query = query.filter(contact_tag=contact_tag)
            
        # Get lists and cache them
        target_lists = list(query.select_related('contact', 'userphone'))
        cache.set(cache_key, target_lists, timeout=cls.CACHE_TIMEOUT)
        
        return target_lists
    
    def invalidate_cache(self):
        """Invalidate cache for this target list's user"""
        cache_key = f'target_lists_{self.userphone.user_id}_{self.contact_type}_{self.contact_tag}'
        cache.delete(cache_key)
    
    def save(self, *args, **kwargs):
        """Override save to enforce validation and handle cache"""
        self.full_clean()
        super().save(*args, **kwargs)
        self.invalidate_cache()  # Clear cache on save

    def get_contacts(self):
        """
        Get contacts associated with this target list using the appropriate resolver
        based on contact_type. Results are cached to prevent repeated API/DB calls.
        """
        from messageShooter.resolvers.get_contacts import get_contact_whatsapp, get_contact_appointment
        import logging
        from django.core.cache import cache
        
        logger = logging.getLogger(__name__)
        
        # Generate cache key based on target list attributes
        cache_key = f'target_list_contacts_{self.id}_{self.contact_type}_{self.contact_tag}'
        
        # Try to get from cache first
        cached_contacts = cache.get(cache_key)
        if cached_contacts is not None:
            logger.debug(f"Using cached contacts for target list {self.id}")
            return cached_contacts
            
        # If not in cache, fetch contacts based on type
        if self.contact_type == 'Whatsapp':
            contacts = get_contact_whatsapp(self.contact_type, self.contact_tag)
            # Cache for 1 hour since WhatsApp contacts change less frequently
            cache.set(cache_key, contacts, timeout=3600)
            return contacts
            
        elif self.contact_type == 'Appointment':
            # Get user from userphone
            if self.userphone and self.userphone.user:
                user = self.userphone.user
                logger.info(f"Getting appointments for user {user.email}")
                contacts = get_contact_appointment(self.contact_type, self.contact_tag, user=user)
                # Cache for 5 minutes since appointments change more frequently
                cache.set(cache_key, contacts, timeout=300)
                return contacts
            else:
                logger.error(f"Missing user for appointment processing in target list {self.id}")
                return []
                
        return []
        
    def invalidate_contacts_cache(self):
        """Invalidate the contacts cache for this target list"""
        from django.core.cache import cache
        cache_key = f'target_list_contacts_{self.id}_{self.contact_type}_{self.contact_tag}'
        cache.delete(cache_key)

    class Meta:
        ordering = ['priority', 'sequence_order', 'created_at']  # FIFO ordering
        indexes = [
            models.Index(fields=['contact_type', 'contact_tag']),
        ]
        

    def __str__(self):
        return f"Target List {self.id} - {self.contact_tag}"
