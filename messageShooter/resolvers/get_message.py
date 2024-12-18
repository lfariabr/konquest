# according to contact type, counter, contact tag, 
# grab message from core>message

from core.models.message import Message
from django.core.exceptions import ObjectDoesNotExist
from messageShooter.resolvers.get_days_interval import calculate_interval
from django.utils import timezone

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

def customize_message_text(message_text, appointment_data):
    """
    Customize message text with appointment details
    Args:
        message_text: Original message text with placeholders
        appointment_data: Dict with appointment details
    Returns:
        Customized message text
    """
    if not message_text or not appointment_data:
        return message_text
        
    # Get values from appointment data
    store_name = appointment_data.get("store_name", "").capitalize()
    customer_name = appointment_data.get("customer_name", "").split()[0].capitalize()
    employee_name = appointment_data.get("employee_name", "").split()[0].capitalize()
    address = appointment_data.get("address", "")
    
    # Format appointment time
    appointment_time = appointment_data.get("appointment_date")
    if isinstance(appointment_time, timezone.datetime):
        date_str = appointment_time.strftime('%d/%m/%Y')
        time_str = appointment_time.strftime('%H:%M')
    else:
        try:
            appointment_time = timezone.datetime.strptime(str(appointment_time), '%Y-%m-%d %H:%M:%S')
            date_str = appointment_time.strftime('%d/%m/%Y')
            time_str = appointment_time.strftime('%H:%M')
        except:
            date_str = ""
            time_str = ""
    
    # Replace placeholders
    replacements = {
        "[nome]": customer_name,
        "[prestador]": employee_name,
        "[data]": date_str,
        "[hora]": time_str,
        "[unidade]": store_name,
        "[address]": address
    }
    
    for placeholder, value in replacements.items():
        message_text = message_text.replace(placeholder, value)
    
    return message_text

def get_message_for_interval(contact_type, relationship_tag=None, counter=0, days_interval=None, appointment_status_label=None, appointment_data=None):
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
    if contact_type != "Appointment" or days_interval is None:
        # For non-appointment messages or when days_interval not provided,
        # fall back to counter-based selection
        return get_message(contact_type, relationship_tag, counter)
    
    # For appointments, use days_interval and status to select message
    message = None
    
    if appointment_status_label == "Agendado" and days_interval == 0:
        message = Message.objects.filter(
            relationship_tag=relationship_tag,
            counter=days_interval
        ).first()
    
    elif appointment_status_label == "Agendado" and days_interval == 1:
        message = Message.objects.filter(
            relationship_tag=relationship_tag,
            counter=days_interval
        ).first()
    
    elif appointment_status_label == "Agendado" and days_interval == 2:
        message = Message.objects.filter(
            relationship_tag=relationship_tag,
            counter=days_interval
        ).first()
    
    elif appointment_status_label == "Confirmado" and days_interval == 0:
        message = Message.objects.filter(
            relationship_tag=relationship_tag,
            counter=days_interval
        ).first()
    
    elif appointment_status_label == "Confirmado" and days_interval == 1:
        message = Message.objects.filter(
            relationship_tag=relationship_tag,
            counter=days_interval
        ).first()
    
    # If message found and appointment data provided, customize message text
    if message and appointment_data:
        message.text = customize_message_text(message.text, appointment_data)
    
    return message