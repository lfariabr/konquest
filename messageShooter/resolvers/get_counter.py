# if contact_type = whatsapp, counter = Count sent messages to number to specific tag
# if contact_type = appointment, counter = DaysToAppoitment (positive or negative in case of NPS)

from messageShooter.resolvers.get_contacts import get_contact_whatsapp, get_contact_appointment
from core.models.messagelog import MessageLogs
from apiCrm.models.appointment import Appointment
from django.utils import timezone
from datetime import timedelta

def get_counter_whatsapp(phone, contact_tag=None):
    """
    For WhatsApp contacts, counter is the number of messages sent for this tag
    This helps in sequence messaging (e.g., first message, follow-up, final reminder)
    
    Args:
        phone: Contact's phone number
        contact_tag: Tag to filter messages by
    Returns:
        Number of messages sent to this contact with this tag
    """
    from core.models.messagelog import MessageLogs
    
    # Filter by phone and tag, only count sent messages
    logs = MessageLogs.objects.filter(
        contact__phone=phone,
        relationship_tag=contact_tag,  # Use relationship_tag here since that's the database field
        status__in=['sent']
    )
    
    return logs.count()

def bulk_get_counter_whatsapp(phones, contact_tag=None):
    """
    Bulk fetch counters for multiple WhatsApp phone numbers
    Args:
        phones: List of phone numbers
        contact_tag: Tag to filter messages by
    Returns:
        Dict mapping phone numbers to their message counters
    """
    from core.models.messagelog import MessageLogs
    from django.db.models import Count
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Fetching counters for {len(phones)} phones with tag {contact_tag}")
    logger.info(f"Sample phones: {phones[:5]}")
    
    # Get counts for all phones in a single query
    counters = MessageLogs.objects.filter(
        contact__phone__in=phones,
        relationship_tag=contact_tag,  
        status__in=['sent'] # change this
    ).values('contact__phone').annotate(
        counter=Count('id')
    )
    
    # Log the raw SQL query
    logger.info(f"SQL Query: {str(counters.query)}")
    
    # Log the results
    counter_list = list(counters)
    logger.info(f"Found {len(counter_list)} phones with messages")
    if counter_list:
        logger.info(f"Sample results: {counter_list[:5]}")
    
    # Convert to phone -> counter dict, defaulting to 0 for phones without messages
    result = {
        phone: next(
            (c['counter'] for c in counter_list if c['contact__phone'] == phone),
            0
        )
        for phone in phones
    }
    
    # Log some sample results
    sample_results = {k: v for k, v in list(result.items())[:5]}
    logger.info(f"Sample final results: {sample_results}")
    
    return result

def get_counter_appointment(phone, relationship_tag=None):
    """
    For Appointment contacts, counter = number of messages sent for this tag / contact.
    This helps in sequence messaging (e.g., first message, follow-up, final reminder)
    
    - Args: phone: Contact's phone number + contact_tag: Tag to filter messages by
    - Returns: Number of messages sent to this contact with this tag
    """
    from core.models.messagelog import MessageLogs
    
    # Filter by phone and tag, only count sent messages
    logs = MessageLogs.objects.filter(
        contact__phone=phone,
        relationship_tag=contact_tag,  # Use relationship_tag here since that's the database field
        status__in=['sent']
    )
    return logs.count()

#TODO NOT IN USE...
def bulk_get_counter_appointment(phones, relationship_tag=None):
    """
    Bulk fetch appointment counters for multiple phone numbers
    Args:
        phones: List of phone numbers
        relationship_tag: Tag determining counter logic
    Returns:
        Dict mapping phone numbers to their counters based on appointment status
    """
    from apiCrm.models.appointment import Appointment
    from django.utils import timezone
    from datetime import timedelta
    
    now = timezone.now()
    counters = {}
    
    if relationship_tag == "NPS":
        # For NPS, counter is always 7 (days since appointment)
        return {phone: 7 for phone in phones}
    
    elif relationship_tag == "Reminder":
        # Get all scheduled appointments for these phones
        appointments = Appointment.objects.filter(
            customer_phone__in=phones,
            status="Scheduled",
            appointment_date__gte=now
        ).values('customer_phone', 'appointment_date')
        
        # Calculate days until appointment for each phone
        for phone in phones:
            apt = next((
                a for a in appointments 
                if a['customer_phone'] == phone
            ), None)
            
            if apt:
                days_until = (apt['appointment_date'].date() - now.date()).days
                counters[phone] = min(days_until, 7)  # Cap at 7 days
            else:
                counters[phone] = 0
                
    elif relationship_tag == "Reschedule":
        # Get reschedule counts for all phones
        from core.models.messagelog import MessageLogs
        reschedule_counts = MessageLogs.objects.filter(
            contact__phone__in=phones,
            message__relationship_tag="Reschedule",
            status__in=['sent']
        ).values('contact__phone').annotate(
            counter=Count('id')
        )
        
        # Map counts to phones
        counters = {
            phone: next(
                (c['counter'] for c in reschedule_counts if c['contact__phone'] == phone),
                0
            )
            for phone in phones
        }
        
    elif relationship_tag == "Google My Business":
        # For Google My Business reviews, counter is always 0
        return {phone: 0 for phone in phones}
    
    return counters