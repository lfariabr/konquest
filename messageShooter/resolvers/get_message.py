# according to contact type, counter, contact tag, 
# grab message from core>message

from core.models.message import Message
from django.core.exceptions import ObjectDoesNotExist

def get_message(contact_type, contact_tag=None, counter=0):
    """
    Get appropriate message based on:
    - Contact type (WhatsApp/Appointment)
    - Contact tag (Preenchimento/Botox/NPS/etc.)
    - Counter (sequence number or days)
    
    Message selection logic:
    1. WhatsApp messages: Selected by tag and sequence (counter)
       - Preenchimento/Botox: Sequential messages (1st contact, follow-up, etc.)
    
    2. Appointment messages: Selected by tag and timing
       - Reminder: Different messages for different days before appointment
       - NPS: 7-day follow-up message
       - Reschedule: Messages based on number of reschedule attempts
       - Google My Business: Review request message
    """
    try:
        # Get message matching all criteria
        message = Message.objects.get(
            relationship_type=contact_type,
            relationship_tag=contact_tag,
            counter=counter
        )
        return message
    
    except ObjectDoesNotExist:
        # If no exact match, try to get default message for this tag
        try:
            message = Message.objects.get(
                relationship_type=contact_type,
                relationship_tag=contact_tag,
                counter=0  # Default message
            )
            return message
        except ObjectDoesNotExist:
            return None

    #TODO double check...