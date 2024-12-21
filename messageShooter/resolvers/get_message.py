# according to contact type, counter, contact tag, 
# grab message from core>message

from core.models.message import Message
from django.core.exceptions import ObjectDoesNotExist
from messageShooter.resolvers.get_days_interval import calculate_interval
import logging

def get_message(contact_type, relationship_tag=None, counter=0):
    """
    Get message based on contact type, relationship tag, and counter
    """
    logger = logging.getLogger(__name__)
    
    logger.info(f"Getting message for type={contact_type}, tag={relationship_tag}, counter={counter}")
    
    # Get base message by tag and counter
    message = Message.objects.filter(
        relationship_tag=relationship_tag,  # This matches the database field name
        counter=counter
    ).first()
    
    if not message:
        logger.info(f"No message found for counter={counter}, falling back to counter=0")
        message = Message.objects.filter(
            relationship_tag=relationship_tag,  # This matches the database field name
            counter=0
        ).first()
    
    if message:
        logger.info(f"Found message id={message.id} for {relationship_tag}")
    else:
        logger.warning(f"No message found for {relationship_tag} (counter={counter})")  
        
    return message

def get_message_original(contact_type, relationship_tag=None, counter=0):
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

def customize_message_text(message_text, variables):
    """
    Customize message text by replacing variables
    Args:
        message_text: original text with placeholders
        variables: dictionary containing replacement values
    Returns:
        Customized message text
    """
    if not message_text or not variables:
        return message_text
    
    # Replace variables that exist in the dict
    for placeholder, value in variables.items():
        if value:  # Only replace if we have a value
            message_text = message_text.replace(placeholder, str(value))
            
    return message_text

def get_message_for_interval(contact_type, 
                            relationship_tag=None,
                            counter=0,
                            days_interval=None,
                            appointment_status_label=None,
                            appointment_data=None):
    """
    Get message based on days until appointment and appointment status
    Args:
        contact_type: Type of contact (WhatsApp/Appointment)
        relationship_tag: Tag determining message type
        counter: Message counter (used for non-appointment messages)
        days_interval: Days until appointment (positive if appointment is in future)
        appointment_status_label: Status of the appointment (e.g., "Agendado", "Confirmado")
        appointment_data: Dict with appointment details for message customization
    Returns:
        Message object or None if no matching message found
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Getting appointment message: status={appointment_status_label}, days_interval={days_interval}")
    
    # For appointments, use days_interval and status to select message
    message = None
    
    if days_interval is None:
        logger.warning("days_interval is None, cannot get appointment message")
        return None
        
    if appointment_status_label == "Agendado":
        if days_interval in [0, 1, 2]:  # Common cases
            message = Message.objects.filter(
                relationship_tag=relationship_tag,
                counter=days_interval
            ).first()
            
    elif appointment_status_label == "Confirmado" and days_interval == 0:
        message = Message.objects.filter(
            relationship_tag=relationship_tag,
            counter=days_interval
        ).first()
        
    if not message:
        logger.info(f"No specific message found for status={appointment_status_label}, days={days_interval}")
        # Try to get a default message for this status
        message = Message.objects.filter(
            relationship_tag=relationship_tag,
            counter=0
        ).first()
        
    if message:
        logger.info(f"Found appointment message id={message.id}")
    else:
        logger.warning(f"No message found for appointment: status={appointment_status_label}, days={days_interval}")
        
    return message