# if contact_type = whatsapp > get Contacts order FIFO
# if contact_type = whatsapp + contact_tag[Botox] > get Contact Botox order FIFO

# if contact_type > get Appointment
# if contact_type = Appointment + contact_tag[Reschedule] > get Appointment Reschedule

from core.models.contact import Contact
from apiCrm.models.appointment import Appointment
from django.utils import timezone
from datetime import timedelta

def get_contact_whatsapp(contact_type, contact_tag=None):
    """
    Get WhatsApp contacts based on tag, ordered by creation date (FIFO).
    If a contact exists with a different tag, it will be included and its tag
    will be updated when creating the target list.
    """
    if contact_type != "Whatsapp":
        return []

    # First try to find contacts that already have the right tag
    contacts = Contact.objects.filter(
        source="Whatsapp",
        relationship_tag=contact_tag,
        status__in=['landing page', 'active']
    ).order_by('created_at')[:500]  # Limit to 500 as per comment in queue_resolver
    
    # If we found contacts, return them
    if contacts.exists():
        return contacts
    
    # If no contacts found, look for any contact with this source and status
    # The tag will be updated when creating the target list
    contacts = Contact.objects.filter(
        source="Whatsapp",
        status__in=['landing page', 'active']
    ).order_by('created_at')[:500]
    
    return contacts

#TODO complement accordingly to specific case scenarios... 
# NPS: appointments "Atendido" in is_assessment == yes
# Reschedule: appointments "FALTA" in assessment == yes in other appointments == no
# ... 
def get_contact_appointment(contact_type, contact_tag=None):
    """
    Get appointments based on tag and status
    For NPS: appointments from 7 days ago
    For Reminder: appointments in next 24 hours
    For Reschedule: appointments with reschedule status
    For Google My Business: completed appointments from last 24 hours
    """
    if contact_type != "Appointment":
        return []

    now = timezone.now()
    
    if contact_tag == "NPS":
        # Get appointments from 7 days ago
        seven_days_ago = now - timedelta(days=7)
        return Appointment.objects.filter(
            appointment_date__date=seven_days_ago.date(),
            status="Completed"
        ).order_by('created_at')
    
    elif contact_tag == "Reminder":
        # Get appointments in next 24 hours
        tomorrow = now + timedelta(days=1)
        return Appointment.objects.filter(
            appointment_date__range=(now, tomorrow),
            status="Scheduled"
        ).order_by('appointment_date')
    
    elif contact_tag == "Reschedule":
        return Appointment.objects.filter(
            status="Reschedule"
        ).order_by('created_at')
    
    elif contact_tag == "Google My Business":
        # Get completed appointments from last 24 hours
        yesterday = now - timedelta(days=1)
        return Appointment.objects.filter(
            appointment_date__range=(yesterday, now),
            status="Completed"
        ).order_by('-appointment_date')
    
    return []
