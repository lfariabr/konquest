# according to contact type, counter, contact tag, 
# grab message from core>message

from core.models.message import Message
from django.core.exceptions import ObjectDoesNotExist
from messageShooter.resolvers.get_days_interval import calculate_interval
import logging

def get_message(contact_type, relationship_tag=None, counter=0):
    """
    Get message based on contact type, relationship tag, and counter
    - Contact type (WhatsApp/Appointment)
    - Relationship tag (Preenchimento/Botox/NPS/etc.)
    - Counter (sequence number or days)
    """
    logger = logging.getLogger(__name__)
    
    logger.info(f"Getting message for type={contact_type}, tag={relationship_tag}, counter={counter}")
    
    # Get base message by tag and counter
    message = Message.objects.filter(
        relationship_tag=relationship_tag,  # This matches the database field name
        counter=counter
    ).first()
    
    if not message:
        logger.info(f"No message found for counter={counter}")
    
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
    Counter encoding:
    - Agendado: days_interval (0, 1, 2)
    - Confirmado: days_interval + 100 (e.g., 100 for day 0, 101 for day 1)
    - Cancelado: days_interval + 200
    - Default fallback: 0
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Getting appointment message: status={appointment_status_label}, days_interval={days_interval}")
    
    message = None
    
    if days_interval is None:
        logger.warning("days_interval is None, cannot get appointment message")
        return None
        
    # Encode status into counter
    if appointment_status_label == "Agendado" and days_interval in [0, 1, 2]:
        encoded_counter = days_interval  # 0, 1, 2 for Agendado
        
    elif appointment_status_label == "Confirmado" and days_interval in [0, 1, 2]:
        encoded_counter = days_interval + 100  # 100, 101, 102 for Confirmado
        
    elif appointment_status_label == "Cancelado" and days_interval in [0, 1, 2]:
        encoded_counter = days_interval + 200  # 200, 201, 202 for Cancelado
        
    else:
        encoded_counter = 0  # Default fallback
    
    # Try to get message with encoded counter
    message = Message.objects.filter(
        relationship_tag=relationship_tag,
        counter=encoded_counter
    ).first()
    
    if not message:
        logger.info(f"No specific message found for status={appointment_status_label}, days={days_interval}")
        # Try to get a default message (counter=0)
        message = Message.objects.filter(
            relationship_tag=relationship_tag,
            counter=0
        ).first()
        
    if message:
        logger.info(f"Found appointment message id={message.id}")
    else:
        logger.warning(f"No message found for appointment: status={appointment_status_label}, days={days_interval}")
        
    return message