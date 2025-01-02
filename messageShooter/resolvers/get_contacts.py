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
    stores_include_es_reschedule,
    reminder_desired_status_es,
    reminder_undesired_status_es,
    reschedule_desired_status_es,
    reschedule_undesired_status_es,
    nps_desired_status_es,
    nps_undesired_status_es,
    nps_stores_include_es
)
from messageShooter.resolvers.get_appointment_to_contact import convert_appointment_to_contact


from konquist.settings import CONTACTS_TO_LOAD, CONTACTS_START, CONTACTS_END, CONTACTS_TO_LOAD_APT
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
        
    contacts = Contact.objects.filter(
        source__iexact="Whatsapp",
        relationship_tag=contact_tag,
        # status__in=['landing page', 'active', None],
        is_lead=False,
        is_appointment=False,
    ).order_by('-created_at')[:CONTACTS_TO_LOAD]  
            
            # Option 1:     :CONTACTS_TO_LOAD 
            # Option 2:     CONTACTS_START:CONTACTS_END
    
    count = contacts.count()
    logger.info(f"Found {count} contacts with tag {contact_tag}")
    
    return contacts 
    #TODO think about how to remove duplicates
    
def get_contact_appointment(contact_type, contact_tag, user=None):
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
        procedure_name__in=procedures_es
        # store_name__in=stores_include_es, 
        # Removed "store_name" to get all stores and filter within the contact tag.
    )

    base_query_nps = Appointment.objects.filter(
        store_name__in=nps_stores_include_es
        ).exclude(
            procedure_name__in=procedures_es
    )

    try:
        if contact_tag == 'Reminder':
            """
            - Get appointments in the next 5 days
            - Exclude appointments that are reminder_undesired_status_es in the last AND future 30 days
            """
            # Get appointments in the next 5 days
            five_days_future = now + timedelta(days=5)
            thirty_days_past = now - timedelta(days=30)
            thirty_days_future = now + timedelta(days=30)
            
            # Get all potential appointments
            potential_appointments = base_query.filter(
                Q(status_label__in=reminder_desired_status_es) &
                Q(appointment_date__range=(now, five_days_future)) &
                Q(store_name__in=stores_include_es)
            ).order_by('appointment_date')

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
            ][:CONTACTS_TO_LOAD_APT]

            logger.info(f"Reminder - Found {len(appointments)} appointments between {now} and {five_days_future}")
        
        elif contact_tag == 'Reschedule':
            logger.info("Starting reschedule appointments processing")
            thirty_days_past = now - timedelta(days=30)
            thirty_days_future = now + timedelta(days=30)
            
            # # Get sample of excluded phone numbers
            # excluded_sample = Appointment.objects.filter(
            #     Q(status_label__in=reschedule_undesired_status_es) &
            #     Q(appointment_date__range=(thirty_days_past, thirty_days_future))
            # ).values('customer_phone', 'status_label', 'store_name', 'appointment_date')[:5]
            
            # # Log initial counts
            # total_desired = base_query.filter(
            #     Q(status_label__in=reschedule_desired_status_es) &
            #     Q(store_name__in=stores_include_es_reschedule) &
            #     Q(procedure_name__in=procedures_es) &
            #     Q(appointment_date__lt=now)  # Only past appointments
            # ).count()
            
            # total_excluded = Appointment.objects.filter(
            #     Q(status_label__in=reschedule_undesired_status_es) &
            #     Q(appointment_date__range=(thirty_days_past, thirty_days_future))
            # ).values('customer_phone').distinct().count()
            
            # Step 1: Get potential reschedule appointments with optimized query
            reschedule_appointments = base_query.filter(
                Q(status_label__in=reschedule_desired_status_es) &
                Q(store_name__in=stores_include_es_reschedule) &
                Q(appointment_date__lt=now) &  # Only past appointments
                ~Q(customer_phone__in=Appointment.objects.filter(
                    Q(status_label__in=reschedule_undesired_status_es) &
                    Q(procedure_name__in=procedures_es) &
                    Q(appointment_date__range=(thirty_days_past, thirty_days_future))
                ).values('customer_phone').distinct())
            ).order_by('-appointment_date')[:CONTACTS_TO_LOAD_APT]  # Most recent appointments first

            appointments = list(reschedule_appointments)
            
            # Get sample of included appointments
            # included_sample = appointments[:5]
            
            # logger.info(
            #     f"Reschedule processing completed:\n"
            #     f"- Total potential appointments (before exclusion): {total_desired}\n"
            #     f"- Total excluded phone numbers: {total_excluded}\n"
            #     f"- Final appointments count: {len(appointments)}\n"
            #     f"\nSAMPLE OF EXCLUDED APPOINTMENTS:\n"
            #     f"{'='*50}\n" +
            #     '\n'.join([f"Phone: {apt['customer_phone']} | Status: {apt['status_label']} | "
            #               f"Store: {apt['store_name']} | Date: {apt['appointment_date']}"
            #               for apt in excluded_sample]) +
            #     f"\n{'='*50}\n"
            #     f"\nSAMPLE OF INCLUDED APPOINTMENTS:\n"
            #     f"{'='*50}\n" +
            #     '\n'.join([f"Phone: {apt.customer_phone} | Status: {apt.status_label} | "
            #               f"Store: {apt.store_name} | Date: {apt.appointment_date}"
            #               for apt in included_sample]) +
            #     f"\n{'='*50}\n"
            #     f"\nTime window: {thirty_days_past} to {thirty_days_future}\n"
            #     f"Desired statuses: {reschedule_desired_status_es}\n"
            #     f"Undesired statuses: {reschedule_undesired_status_es}\n"
            #     f"Included stores: {stores_include_es_reschedule}"
            # )

        # elif contact_tag == 'Reschedule':
        #     thirty_days_past = now - timedelta(days=30)
        #     thirty_days_future = now + timedelta(days=30)
            
        #     # Potential reschedule appointments
        #     reschedule_appointments = base_query.filter(
        #         Q(status_label__in=reschedule_desired_status_es) &
        #         Q(store_name__in=stores_include_es_reschedule)
        #     ).order_by('appointment_date')

        #     # Exclude appointments with undesired statuses
        #     excluded_appointments = Appointment.objects.filter(
        #         Q(status_label__in=reschedule_undesired_status_es) &
        #         Q(appointment_date__range=(thirty_days_past, thirty_days_future))
        #     ).values('customer_phone')

        #     # Create set of excluded phone numbers
        #     excluded_phones = set(excluded_appointments.values_list('customer_phone', flat=True))

        #     # Final filtering
        #     appointments = [
        #         apt for apt in reschedule_appointments 
        #         if apt.customer_phone not in excluded_phones
        #     ][:CONTACTS_TO_LOAD_APT]

            logger.info(f"Reschedule - Found {len(appointments)} appointments")

        elif contact_tag == 'NPS':
            
            # Define NPS period: past 2 days
            last_2_days = now - timedelta(days=4)
            
            # Get all potential appointments
            nps_appointments = base_query_nps.filter(
                    Q(status_label__in=nps_desired_status_es) &
                    Q(appointment_date__range=(last_2_days, now)) &
                    Q(store_name__in=nps_stores_include_es)
                ).order_by('appointment_date')

            # Create a dictionary to keep track of unique phone numbers
            # Keep only the first (earliest) appointment for each phone
            unique_appointments = {}
            for apt in nps_appointments:
                if apt.customer_phone not in unique_appointments:
                    unique_appointments[apt.customer_phone] = apt

            # Convert back to list and apply limit
            appointments = list(unique_appointments.values())[:CONTACTS_TO_LOAD_APT]

            logger.info(f"NPS - Found {len(nps_appointments)} total appointments, {len(appointments)} unique appointments")

        else:
            # Default case: return all relevant appointments
            appointments = base_query.order_by('appointment_date')[:CONTACTS_TO_LOAD_APT]
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