# if contact_type > get Appointment
# if contact_type = Appointment + contact_tag[Reminder] > get Appointment Reminder

import logging
from django.conf import settings
from django.db.models import Q
from datetime import timedelta
from django.utils import timezone
from core.models.contact import Contact
from apiCrm.models.appointment import Appointment
from messageShooter.utils.is_appointment_es import (procedures_es, 
                                                stores_include_es, 
                                                reminder_desired_status_es,
                                                reminder_undesired_status_es)
from messageShooter.resolvers.get_appointment_to_contact import convert_appointment_to_contact
from konquist.settings import CONTACTS_TO_LOAD

logger = logging.getLogger(__name__)

def get_contact_appointment_reminder(contact_type, contact_tag, user=None):
    """
    Get appointments based on specific relationship tag rules
    - Args: 
        contact_tag (str, optional): Tag to filter appointments ('Reminder', 'NPS', 'Reschedule')
        user: User instance to associate with created contacts
    - Returns: List of Contact instances derived from appointments
    """
    logger = logging.getLogger(__name__)

    if contact_type != "Appointment":
        return []

    if not user:
        logger.error("No user provided for appointment processing")
        return []

    now = timezone.now()
    logger = logging.getLogger(__name__)
    
    # Base query with common filters
    base_query = Appointment.objects.filter(
        store_name__in=stores_include_es,
        procedure_name__in=procedures_es
    )

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
        
        else:
            # Default case: return all relevant appointments
            appointments = base_query.order_by('appointment_date')[:CONTACTS_TO_LOAD]
            logger.info(f"Default - Found {len(appointments)} appointments")
            
        # Convert appointments to contacts
        contacts = []
        for appointment in appointments:
            contact = convert_appointment_to_contact(appointment, contact_tag, user)
            if contact:
                contacts.append(contact)
            
        logger.info(f"Converted {len(contacts)} appointments to contacts with tag '{contact_tag}'")
        return contacts

    except Exception as e:
        logger.error(f"Error getting appointments: {str(e)}")
        return []

# python manage.py shell
"""
from messageShooter.resolvers.get_contacts_reminder import get_contact_appointment_reminder
from core.models.user import kUser  # Change this line
user = kUser.objects.first()
contacts = get_contact_appointment_reminder("Appointment", "Reminder", user=user)

# Print results
print(f"\nFound {len(contacts)} contacts")
for contact in contacts:
    print(f"\nStore: {contact.store_name}")  # Note: using store_name instead of store
    print(f"Status: {contact.status_label}")
    print(f"Customer: {contact.customer_name}")
    print(f"Phone: {contact.customer_phone}")
    print(f"Date: {contact.appointment_date}")
"""