# if contact_type = whatsapp > get Contacts order FIFO
# if contact_type = whatsapp + contact_tag[Botox] > get Contact Botox order FIFO

# if contact_type > get Appointment
# if contact_type = Appointment + contact_tag[Reschedule] > get Appointment Reschedule

import logging
from django.conf import settings
from django.db.models import Q
from datetime import timedelta
from django.utils import timezone
from core.models.contact import Contact
from apiCrm.models.appointment import Appointment
from messageShooter.utils.is_appointment_es import (
    procedures_es, 
    stores_exclude_es, 
    stores_include_es, 
    intervals_es,
    reminder_desired_status_es,
    reminder_undesired_status_es,
    reschedule_desired_status_es,
    reschedule_undesired_status_es
)

from konquist.settings import CONTACTS_TO_LOAD

number_of_contacts = settings.CONTACTS_TO_LOAD
logger = logging.getLogger(__name__)

def get_contact_whatsapp(contact_type, contact_tag):
    """
    Get WhatsApp contacts based on tag, ordered by creation date (FIFO).
    If a contact exists with a different tag, it will be included and its tag
    will be updated when creating the target list.
    Returns only unique contacts by phone number, taking the earliest created contact.
    """
    if contact_type != "Whatsapp":
        return []

    from django.db.models import Min, Subquery, OuterRef

    # Get the earliest created contact for each phone number
    earliest_contacts = Contact.objects.filter(
        source__iexact="Whatsapp",  # Case-insensitive match
        relationship_tag=contact_tag,
        status__in=['landing page', 'active'],
        is_lead=False,
        is_appointment=False,
    ).values('phone').annotate(
        min_id=Min('id')
    ).values('min_id')

    contacts = Contact.objects.filter(
        id__in=Subquery(earliest_contacts)
    ).order_by('-created_at')[:CONTACTS_TO_LOAD]
    
    count = contacts.count()
    logger.info(f"Found {count} contacts with tag {contact_tag}")
    return contacts
    
def get_contact_appointment(contact_type, contact_tag):
    """
    Get appointments based on specific relationship tag rules
    - Args: contact_tag (str, optional): Tag to filter appointments ('Reminder', 'NPS', 'Reschedule')
    - Returns: dict: Filtered appointments matching the specified relationship tag
    """
    if contact_type != "Appointment":
        return []

    now = timezone.now()
    filtered_appointments = {}
    
    # Base query with common filters
    base_query = Appointment.objects.filter(
        store_name__in=stores_include_es,
        procedure_name__in=procedures_es
    )

    # Reminder, to test:
    # python manage.py shell
    # from messageShooter.resolvers.get_contacts import get_contact_appointment
    # get_contact_appointment('Reminder')

    try:
        if contact_tag == 'Reminder':
            # Get appointments in the next 5 days
            five_days_future = now + timedelta(days=5)
            thirty_days_past = now - timedelta(days=30)
            thirty_days_future = now + timedelta(days=30)
            
            # Get all potential appointments
            potential_appointments = base_query.filter(
                Q(status_label__in=reminder_desired_status_es) &
                Q(appointment_date__range=(now, five_days_future))  # Specific 5-day window
            )

            # Get excluded appointments by existing customer_phone
            excluded_appointments = Appointment.objects.filter(
                Q(status_label__in=reminder_undesired_status_es) &
                Q(procedure_name__in=procedures_es) &
                Q(appointment_date__range=(thirty_days_past, thirty_days_future))
            ).values('customer_phone')

            # Create set exclusion criteria
            excluded_phones = set(excluded_appointments.values_list('customer_phone', flat=True))

            # Filter appointments that don't match exclusion criteria
            appointments = [
                apt for apt in potential_appointments 
                if apt.customer_phone not in excluded_phones
            ][:CONTACTS_TO_LOAD]

            logger.info(f"Reminder - Found {len(appointments)} appointments between {now} and {five_days_future}")

        elif contact_tag == 'NPS':
            # NPS specific logic
            three_days_past = now - timedelta(days=3)
            five_days_past = now - timedelta(days=5)
            
            # Appointments from 3 days ago
            nps_appointments = base_query.filter(
                Q(appointment_date__range=(three_days_past, now)) &
                ~Q(status_label__in=['Atendido', 'Falta', 'Cancelado']) # Create desired_nps_status
            ).order_by('appointment_date')

            # Verify no recent undesired status
            appointments = [
                apt for apt in nps_appointments
                if not Appointment.objects.filter(
                    customer_phone=apt.customer_phone,
                    status_label__in=['Atendido', 'Falta', 'Cancelado'], # Create undesired_nps_status
                    appointment_date__range=(five_days_past, now)
                ).exists()
            ][:CONTACTS_TO_LOAD]

            logger.info(f"NPS - Found {len(appointments)} appointments between {three_days_past} and {now}")

        elif contact_tag == 'Reschedule':
            # Reschedule specific logic
            thirty_days_past = now - timedelta(days=30)
            thirty_days_future = now + timedelta(days=30)
            
            # Potential reschedule appointments
            reschedule_appointments = base_query.filter(
                Q(status_label__in=reschedule_desired_status_es)
            ).order_by('appointment_date')

            # Exclude appointments with undesired statuses
            excluded_appointments = Appointment.objects.filter(
                Q(status_label__in=reschedule_undesired_status_es) &
                Q(appointment_date__range=(thirty_days_past, thirty_days_future))
            )

            # Create set of excluded phone numbers
            excluded_phones = set(excluded_appointments.values_list('customer_phone', flat=True))

            # Final filtering
            appointments = [
                apt for apt in reschedule_appointments 
                if apt.customer_phone not in excluded_phones
            ][:CONTACTS_TO_LOAD]

            logger.info(f"Reschedule - Found {len(appointments)} appointments")

        else:
            # Default case: return all relevant appointments
            appointments = base_query.order_by('appointment_date')[:CONTACTS_TO_LOAD]
            logger.info(f"Default - Found {len(appointments)} appointments")
            
        # Convert to dictionary format
        for appointment in appointments:
            filtered_appointments[appointment.id_crm] = {
                'customer_name': appointment.customer_name,
                'customer_phone': appointment.customer_phone,
                'store_name': appointment.store_name,
                'procedure_name': appointment.procedure_name,
                'employee_name': appointment.employee_name,
                'status_label': appointment.status_label,
                'appointment_date': appointment.appointment_date,
                'contact_tag': contact_tag or 'Default'
            }

        logger.info(
            f"Retrieved {len(filtered_appointments)} appointments for tag '{contact_tag}'"
        )
        print(appointments)
    
        # print(filtered_appointments)
        
    except Exception as e:
        logger.error(f"Error retrieving appointments for tag '{contact_tag}': {str(e)}")
        raise
    return appointments # appointments # filtered_appointments


def get_contact_nps():
    """
    Grab NPS contacts that gave scoring of 9 or 10 from spreadsheet in the past 2 days.
    Ask for their review on local store Google My Business.
    """
    pass