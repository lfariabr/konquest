# according to contact type, counter, contact tag, 
# grab message from core>message

from core.models.message import Message
from django.core.exceptions import ObjectDoesNotExist
from messageShooter.resolvers.get_days_interval import calculate_interval

def get_message(contact_type, relationship_tag=None, counter=0):
    """
    Get appropriate message based on:
    - Contact type (WhatsApp/Appointment)
    - Relationship tag (Preenchimento/Botox/NPS/etc.)
    - Counter (sequence number or days)
    
    Message selection logic:
    1. WhatsApp messages: Selected by tag and sequence (counter)
       - Preenchimento/Botox: Sequential messages (1st contact, follow-up, etc.)
       - If no message exists for the counter, returns None (no fallback)
    
    2. Appointment messages: Selected by tag and timing
       - Reminder: Different messages for different days before appointment
       - NPS: 7-day follow-up message
       - Reschedule: Messages based on number of reschedule attempts
       - Google My Business: Review request message
    """
    # Get message matching all criteria - no fallback to counter=0
    message = Message.objects.filter(
        relationship_tag=relationship_tag,  # This matches the database field name
        counter=counter
    ).first()
    
    return message

def get_message_for_interval(contact_type, relationship_tag=None, counter=0, calculate_interval=0):
    # Get message matching all criteria - no fallback to counter=0
    message = Message.objects.filter(
        relationship_tag=relationship_tag,  # This matches the database field name
        counter=counter
    ).first()
    
    return message