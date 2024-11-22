# if contact_type = whatsapp, counter = Count sent messages to number to specific tag
# if contact_type = appointment, counter = DaysToAppoitment (positive or negative in case of NPS)

from resolvers.get_contacts import get_contact_whatsapp, get_contact_appointment
from core.models.messagelog import MessageLogs
from core.models.appointment import Appointment
from django.utils import timezone
from datetime import timedelta

def get_counter_whatsapp(contact_type, contact_tag=None):
    """
    For WhatsApp contacts, counter is the number of messages sent for this tag
    This helps in sequence messaging (e.g., first message, follow-up, final reminder)
    """
    if contact_type != "Whatsapp":
        return 0

    return MessageLogs.objects.filter(
        message__relationship_tag=contact_tag,
        status="sent"
    ).count()

#TODO update/test later.
def get_counter_appointment(contact_type, contact_tag=None):
    """
    For appointments, counter depends on the tag:
    - Reminder: Days until appointment (0 = today, 1 = tomorrow)
    - NPS: Days since appointment (7 = week ago)
    - Reschedule: Number of reschedule attempts
    - Google My Business: Always 0 (single message)
    """
    if contact_type != "Appointment":
        return 0

    now = timezone.now()

    if contact_tag == "Reminder":
        # For reminders, return days until appointment
        appointment = Appointment.objects.filter(
            status="Scheduled",
            appointment_date__gte=now
        ).order_by('appointment_date').first()
        
        if appointment:
            days_until = (appointment.appointment_date.date() - now.date()).days
            return min(days_until, 7)  # Cap at 7 days
        return 0

    elif contact_tag == "NPS":
        # For NPS, return days since appointment (typically 7)
        return 7

    elif contact_tag == "Reschedule":
        # For reschedule, return number of reschedule attempts
        return MessageLogs.objects.filter(
            message__relationship_tag="Reschedule",
            status="sent"
        ).count()

    elif contact_tag == "Google My Business":
        # For Google My Business reviews, always send first message
        return 0

    return 0