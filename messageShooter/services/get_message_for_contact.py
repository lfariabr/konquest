import logging
from typing import Tuple, Optional
from core.models.message import Message
from core.models.contact import Contact
from messageShooter.models.target_list import TargetList
from messageShooter.resolvers.get_counter import get_counter_whatsapp
from messageShooter.resolvers.get_message import get_message, get_message_for_interval, customize_message_text
from messageShooter.resolvers.get_days_interval import calculate_interval

logger = logging.getLogger(__name__)

def get_message_for_contact(contact: Contact, target_list: TargetList) -> Tuple[int, Optional[Message]]:
    """
    Get appropriate message for a contact based on contact type and target list
    
    Args:
        contact: Contact object to get message for
        target_list: TargetList object containing message parameters
        
    Returns:
        Tuple of (counter, message)
        counter: Current message counter for this contact
        message: Message object or None if no appropriate message found
    """
    try:
        logger.info(f"Getting message for contact {contact.id} (phone: {contact.phone})")
        
        if target_list.contact_type == "Appointment":
            logger.info(f"📅 Processing appointment message for contact {contact.phone}")
            
            # Get appointment-specific data
            days_interval = calculate_interval(contact.appointment_created_at) if contact.appointment_created_at else None
            logger.info(f"Days until appointment: {days_interval}")
            logger.info(f"Appointment Date: {contact.appointment_created_at}")
     
            message = get_message_for_interval(
                contact_type=target_list.contact_type,
                relationship_tag=target_list.contact_tag,
                counter=0,  # Not used for appointments
                days_interval=days_interval,
                appointment_status_label=contact.appointment_status
            )
            
            # Customize message with contact variables
            if message:
                message.text = customize_message_text(message.text, contact.message_variables)
                
            if target_list.contact_tag == "Reminder" or target_list.contact_tag == "Reschedule":
                logger.info(f"Using days_interval counter: {days_interval} for {target_list.contact_tag}") 
                return days_interval, message
            else:
                counter = get_counter_whatsapp(contact.phone, target_list.contact_tag)
                logger.info(f"Using regular whatsapp counter: {counter} for {target_list.contact_tag}")
                return counter, message
        else:
            counter = get_counter_whatsapp(contact.phone, target_list.contact_tag)
            logger.info(f"💬 Processing WhatsApp message for contact {contact.phone}")
            
            message = get_message(
                contact_type=target_list.contact_type,
                relationship_tag=target_list.contact_tag,
                counter=counter
            )
            
            # Customize message with contact variables
            if message:
                message.text = customize_message_text(message.text, contact.message_variables)
                logger.debug(f"✏️ Customized message for {contact.phone}: {message.text[:50]}...")
            else:
                logger.warning(f"❌ No message found for contact {contact.phone}")
                
            return counter, message
            
    except Exception as e:
        logger.error(f"❌ Error getting message for contact {contact.phone}: {str(e)}", exc_info=True)
        return 0, None