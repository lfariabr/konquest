# if contact_type > get Appointment
# if contact_type = Appointment + contact_tag[Reschedule] > get Appointment Reschedule

import logging
from django.conf import settings
from django.db.models import Q
from datetime import timedelta
from django.utils import timezone
from core.models.contact import Contact
from apiCrm.models.appointment import Appointment
from messageShooter.utils.is_appointment_es import (procedures_es, 
                                                reschedule_desired_status_es,
                                                reschedule_undesired_status_es,
                                                stores_include_es_reschedule)
from messageShooter.resolvers.get_appointment_to_contact import convert_appointment_to_contact
from konquist.settings import CONTACTS_TO_LOAD

logger = logging.getLogger(__name__)

def get_contact_appointment_reschedule(contact_type, contact_tag, user=None):
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
        store_name__in=stores_include_es_reschedule,
        procedure_name__in=procedures_es
    )

    try:
        if contact_tag == 'Reschedule':
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
from messageShooter.resolvers.get_contacts_reschedule import get_contact_appointment_reschedule
from core.models.user import kUser  # Change this line
user = kUser.objects.first()

# Test the function
appointments = get_contact_appointment_reschedule("Appointment", "Reschedule", user)

# Print results
print(f"\nFound {len(appointments)} appointments")
for apt in appointments:
    print(f"\nStore: {apt.store_name}")  # Note: using store_name instead of store
    print(f"Status: {apt.status_label}")
    print(f"Customer: {apt.customer_name}")
    print(f"Phone: {apt.customer_phone}")
    print(f"Date: {apt.appointment_date}")
"""