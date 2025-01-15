# according to contact type, counter, contact tag, 
# grab message from core>message

from core.models.message import Message
from django.core.exceptions import ObjectDoesNotExist
from messageShooter.resolvers.get_days_interval import calculate_interval
from messageShooter.resolvers.get_counter import get_counter_whatsapp, get_counter_appointment
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
    Get encoded counter based on relationship tag, status and days interval.
    
    Reminder Tag:
        - Agendado: 0-2 days (counters 0,1,2)
        - Confirmado: 0-2 days (counters 100,101,102)
    
    Reschedule Tag:
        - Falta: Based on days since missed appointment
            * 1-7 days: counter 300
            * 7-14 days: counter 301
            * 14+ days: counter 302
        - Cancelado: Based on days since cancellation
            * 1-7 days: counter 400
            * 7-14 days: counter 401
            * 14+ days: counter 402
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Getting appointment message: status={appointment_status_label}, days_interval={days_interval}")
    
    if not appointment_status_label:
        return None

    message = None
    
    if days_interval is None:
        logger.warning("days_interval is None, cannot get appointment message")
        return None

    # Tags Mapping    
    reminder_tags = ["Reminder", "ReminderPL", "ReminderIpiranga", "ReminderSantoAmaro"]
    reschedule_tags = ["Reschedule", "ReschedulePL"]

    # Calculate the counter based on tag and interval
    if relationship_tag in reminder_tags:
        if appointment_status_label == "Agendado" and days_interval in [0, 1, 2]:
            counter = days_interval  # 0, 1, 2 for upcoming appointments
        elif appointment_status_label == "Confirmado" and days_interval in [0, 1, 2]:
            counter = days_interval + 100  # 100, 101, 102 for confirmed appointments
        else:
            logger.warning(f"Invalid combination for Reminder: status={appointment_status_label}, days={days_interval}")
            return None  # Invalid combination for Reminder
    
    # Maybe fit in NPS here?
    elif relationship_tag == "NPS":
        if not appointment_data or "phone" not in appointment_data:
            logger.warning("Missing appointment_data or phone for NPS message")
            return None
            
        counter = get_counter_appointment(appointment_data["phone"], "NPS")
        logger.info(f"Using appointment counter {counter} for NPS message")
    
    elif relationship_tag in reschedule_tags:
            if appointment_status_label == "Falta":
                expected_counter = 0
                if -7 < days_interval <= -1:  # Changed to match get_message_for_interval
                    expected_counter = 0      # Recent miss (0-7 days_interval ago)
                elif -14 < days_interval <= -7:
                    expected_counter = 1      # Week-old miss (7-14 days_interval ago)
                elif days_interval <= -14:
                    expected_counter = 2      # Old miss (14+ days_interval ago)
                
                # Only proceed if the actual counter matches what we expect for this period
                if counter != expected_counter:
                    logger.info(f"Counter mismatch - Expected: {expected_counter}, Actual: {counter}. Skipping message.")
                    return None
                
                counter = expected_counter  # Set the counter for message lookup

            elif appointment_status_label == "Cancelado":
                expected_counter = 0
                if -7 <= days_interval <= -1:    # Changed to match get_message_for_interval
                    expected_counter = 0      # Recent cancellation
                elif -14 <= days_interval <= -7:
                    expected_counter = 1      # Week-old cancellation
                elif days_interval <= -14:
                    expected_counter = 2      # Old cancellation
                
                # Only proceed if the actual counter matches what we expect for this period
                if counter != expected_counter:
                    logger.info(f"Counter mismatch - Expected: {expected_counter}, Actual: {counter}. Skipping message.")
                    return None
                
                counter = expected_counter  # Set the counter for message lookup

            else:
                logger.warning(f"Invalid appointment_status_label for Reschedule: appointment_status_label={appointment_status_label}, days={days}")
                return None  # Invalid status for Reschedule
            
    else:
        logger.info(f"Using default counter=0 for tag: {relationship_tag}")
        counter = 0  # Default fallback for other tags
    
    logger.debug(f"Calculated counter={counter} for {relationship_tag} - {appointment_status_label} - {days_interval} days")
    
    # Try to get message with encoded counter
    message = Message.objects.filter(
        relationship_tag=relationship_tag,
        counter=counter
    ).first()
    
    if not message:
        logger.warning(f"No message found for {relationship_tag} (counter={counter}, type={contact_type})")
        return None

    logger.info(f"Found message id={message.id} for {relationship_tag}")        
    return message