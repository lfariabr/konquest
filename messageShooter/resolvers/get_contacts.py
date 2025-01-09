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
from django.core.cache import cache
from apiCrm.models.appointment import Appointment
from messageShooter.utils.is_appointment_es import (
    procedures_es, 
    stores_exclude_es, 
    stores_include_es, 
    intervals_es,
    procedures_pl,
    stores_include_es_reschedule,
    reminder_desired_status_es,
    reminder_undesired_status_es,
    reschedule_desired_status_es,
    reschedule_undesired_status_es,
    nps_desired_status_es,
    nps_undesired_status_es,
    nps_stores_include_es,
    stores_include_pl_reschedule,
    reschedule_desired_status_pl,
    reschedule_undesired_status_pl,
    reschedule_stores_include_pl,
    reminder_desired_status_pl,
    reminder_undesired_status_pl
)
from messageShooter.resolvers.get_appointment_to_contact import convert_appointment_to_contact, convert_appointments_to_contacts_bulk
from datetime import datetime, timedelta
from typing import List
from django.db.models import Min
from django.db.models.query import QuerySet


from konquist.settings import CONTACTS_TO_LOAD, CONTACTS_START, CONTACTS_END, CONTACTS_TO_LOAD_APT
logger = logging.getLogger(__name__)

def get_contact_whatsapp(contact_type: str, contact_tag: str) -> QuerySet:
    """
    Get WhatsApp contacts based on tag, ordered by creation date (FIFO).
    If a contact exists with a different tag, it will be included and its tag
    will be updated when creating the target list.
    
    Args:
        contact_type (str): Type of contact (must be "Whatsapp")
        contact_tag (str): Tag to filter contacts
        
    Returns:
        QuerySet: Unique contacts by phone number from the last 30 days, 
                 taking the earliest created contact
    """
    logger.info(f"Fetching WhatsApp contacts with tag '{contact_tag}'")
    
    if contact_type != "Whatsapp":
        logger.warning(f"Invalid contact type: {contact_type}. Expected 'Whatsapp'")
        return []
    
    # Calculate date 30 days ago with timezone awareness
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Get base queryset with all filters
    contacts = Contact.objects.filter(
        source__iexact="Whatsapp",
        relationship_tag=contact_tag,
        is_lead=False,
        is_appointment=False,
        created_at__gte=thirty_days_ago
    )

    logger.info(
        f"Found {contacts.count()} total contacts from the last 30 days "
        f"with tag '{contact_tag}'"
    )
    
    # Remove duplicates by keeping earliest contact per phone number
    unique_contacts = contacts.values('phone').annotate(
        min_created_at=Min('created_at')
    ).order_by('-min_created_at')
    
    # Get the actual Contact objects with proper limit
    unique_contact_ids = contacts.filter(
        created_at__in=[item['min_created_at'] for item in unique_contacts]
    ).values_list('id', flat=True)
    
    final_contacts = contacts.filter(
        id__in=unique_contact_ids
    ).order_by('-created_at')[:CONTACTS_TO_LOAD]
    
    logger.info(
        f"Found {len(unique_contacts)} unique contacts from the last 30 days "
        f"with tag '{contact_tag}'"
    )
    
    return final_contacts
    
def get_contact_appointment(contact_type, contact_tag, user=None):
    """
    Get appointments based on specific relationship tag rules
    - Args: 
        contact_tag (str, optional): Tag to filter appointments ('Reminder', 'NPS', 'Reschedule')
        user: User instance to associate with created contacts
    - Returns: List of Contact instances derived from appointments
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing contacts with tag {contact_tag}")

    if contact_type != "Appointment" or not user:
        logger.error("Invalid contact type or no user provided")
        return []

    now = timezone.now()
    
    # Try to get from cache first for all types
    cache_key = f'appointments_{contact_tag}_{user.id}'
    cached_contacts = cache.get(cache_key)
    if cached_contacts is not None:
        logger.info(f"Using cached contacts for {contact_tag}")
        return cached_contacts

    # Base queries with optimized filters
    base_query = Appointment.objects.filter(procedure_name__in=procedures_es)
    
    base_query_nps = Appointment.objects.filter(
        store_name__in=nps_stores_include_es
    ).exclude(procedure_name__in=procedures_es)
    
    base_query_pl = Appointment.objects.filter(
        store_name__in=stores_include_pl_reschedule,
        procedure_name__in=procedures_pl
    )

    try:
        if contact_tag == 'Reminder':
            # Optimize time ranges
            five_days_future = now + timedelta(days=5)
            thirty_days_past = now - timedelta(days=30)
            thirty_days_future = now + timedelta(days=30)
            
            # Get excluded phones first (can be cached)
            excluded_cache_key = f'excluded_phones_reminder_{user.id}'
            excluded_phones = cache.get(excluded_cache_key)
            
            if excluded_phones is None:
                excluded_phones = set(Appointment.objects.filter(
                    status_label__in=reminder_undesired_status_es,
                    procedure_name__in=procedures_es,
                    appointment_date__range=(thirty_days_past, thirty_days_future)
                ).values_list('customer_phone', flat=True))
                cache.set(excluded_cache_key, excluded_phones, timeout=3600)
            
            # Get appointments with optimized query
            appointments = base_query.filter(
                status_label__in=reminder_desired_status_es,
                appointment_date__range=(now, five_days_future),
                store_name__in=stores_include_es
            ).exclude(
                customer_phone__in=excluded_phones
            ).order_by('appointment_date')[:CONTACTS_TO_LOAD_APT]
            
            appointments = list(appointments)
            logger.info(f"Reminder - Found {len(appointments)} appointments")
        
        elif contact_tag == 'ReminderPL':
            five_days_future = now + timedelta(days=5)
            thirty_days_past = now - timedelta(days=30)
            thirty_days_future = now + timedelta(days=30)

            # Debug: Count total appointments in PL
            total_pl = Appointment.objects.filter(
                store_name__in=stores_include_pl_reschedule
            ).count()
            logger.info(f"Total appointments in PL: {total_pl}")

            # Debug: Count appointments with desired status
            status_filtered = Appointment.objects.filter(
                store_name__in=stores_include_pl_reschedule,
                status_label__in=reminder_desired_status_pl
            ).count()
            logger.info(f"Appointments with desired status: {status_filtered}")

            # Debug: Count appointments with matching procedures
            procedure_filtered = Appointment.objects.filter(
                store_name__in=stores_include_pl_reschedule,
                procedure_name__in=procedures_pl
            ).count()
            logger.info(f"Appointments with matching procedures: {procedure_filtered}")
            
            # Get excluded phones first (can be cached)
            excluded_cache_key = f'excluded_phones_reminder_pl_{user.id}'
            excluded_phones = cache.get(excluded_cache_key)
            
            if excluded_phones is None:
                excluded_phones = set(Appointment.objects.filter(
                    status_label__in=reminder_undesired_status_pl,
                    procedure_name__in=procedures_pl,
                    appointment_date__range=(thirty_days_past, thirty_days_future)
                ).values_list('customer_phone', flat=True))
                cache.set(excluded_cache_key, excluded_phones, timeout=3600)
            
            # Get appointments with optimized query
            appointments = base_query_pl.filter(
                status_label__in=reminder_desired_status_pl,
                appointment_date__range=(now, five_days_future)
            ).exclude(
                customer_phone__in=excluded_phones
            ).order_by('appointment_date')[:CONTACTS_TO_LOAD_APT]
            
            appointments = list(appointments)
            logger.info(f"ReminderPL - Found {len(appointments)} appointments")
        
        elif contact_tag == 'Reschedule':
            thirty_days_past = now - timedelta(days=30)
            thirty_days_future = now + timedelta(days=30)
            
            # Get excluded phones (cached)
            excluded_cache_key = f'excluded_phones_reschedule_{user.id}'
            excluded_phones = cache.get(excluded_cache_key)
            
            if excluded_phones is None:
                excluded_phones = set(Appointment.objects.filter(
                    status_label__in=reschedule_undesired_status_es,
                    procedure_name__in=procedures_es,
                    appointment_date__range=(thirty_days_past, thirty_days_future)
                ).values_list('customer_phone', flat=True))
                cache.set(excluded_cache_key, excluded_phones, timeout=3600)
            
            # Optimized query with distinct handling
            appointments = base_query.filter(
                status_label__in=reschedule_desired_status_es,
                store_name__in=stores_include_es_reschedule,
                appointment_date__lt=now
            ).exclude(
                customer_phone__in=excluded_phones
            ).order_by('-appointment_date')
            
            # Handle distinct in Python for better compatibility
            seen_phones = set()
            unique_appointments = []
            for apt in appointments:
                if apt.customer_phone not in seen_phones:
                    seen_phones.add(apt.customer_phone)
                    unique_appointments.append(apt)
                if len(unique_appointments) >= CONTACTS_TO_LOAD_APT:
                    break
            
            appointments = unique_appointments
            logger.info(f"Reschedule - Found {len(appointments)} appointments")

        elif contact_tag == 'ReschedulePL':
            thirty_days_past = now - timedelta(days=30)
            thirty_days_future = now + timedelta(days=30)

            # Debug: Count total appointments in PLÁSTICA
            total_pl = Appointment.objects.filter(
                store_name__in=stores_include_pl_reschedule
            ).count()
            logger.info(f"ReschedulePL - Total appointments in PLÁSTICA: {total_pl}")
            
            # Debug: Count appointments with desired status
            status_filtered = Appointment.objects.filter(
                store_name__in=stores_include_pl_reschedule,
                status_label__in=reschedule_desired_status_pl
            ).count()
            logger.info(f"ReschedulePL - Appointments with status {reschedule_desired_status_pl}: {status_filtered}")
            
            # Debug: Count appointments with matching procedures
            procedure_filtered = Appointment.objects.filter(
                store_name__in=stores_include_pl_reschedule,
                status_label__in=reschedule_desired_status_pl,
                procedure_name__in=procedures_pl
            ).count()
            logger.info(f"ReschedulePL - Appointments with matching procedures: {procedure_filtered}")
            
            # Get excluded phones (cached)
            excluded_cache_key = f'excluded_phones_reschedule_{user.id}'
            excluded_phones = cache.get(excluded_cache_key)
            
            if excluded_phones is None:
                excluded_phones = set(Appointment.objects.filter(
                    status_label__in=reschedule_undesired_status_pl,
                    procedure_name__in=procedures_pl,
                    appointment_date__range=(thirty_days_past, thirty_days_future)
                ).values_list('customer_phone', flat=True))
                cache.set(excluded_cache_key, excluded_phones, timeout=3600)
            
            # Optimized query with distinct handling
            appointments = base_query_pl.filter(
                status_label__in=reschedule_desired_status_pl,
                store_name__in=reschedule_stores_include_pl,
                appointment_date__lt=now
            ).exclude(
                customer_phone__in=excluded_phones
            ).order_by('-appointment_date')
            
            # Handle distinct in Python for better compatibility
            seen_phones = set()
            unique_appointments = []
            for apt in appointments:
                if apt.customer_phone not in seen_phones:
                    seen_phones.add(apt.customer_phone)
                    unique_appointments.append(apt)
                if len(unique_appointments) >= CONTACTS_TO_LOAD_APT:
                    break
            
            appointments = unique_appointments
            logger.info(f"ReschedulePL - Found {len(appointments)} appointments")
        
        elif contact_tag == 'NPS':
            # Define NPS period
            last_2_days = now - timedelta(days=2)
            
            # Debug: Count total appointments before filtering
            total_appointments = Appointment.objects.filter(
                appointment_date__range=(last_2_days, now)
            ).count()
            logger.info(f"Total appointments in last 10 days: {total_appointments}")
            
            # Debug: Count after store filter
            store_filtered = Appointment.objects.filter(
                appointment_date__range=(last_2_days, now),
                store_name__in=nps_stores_include_es
            ).count()
            logger.info(f"Appointments after store filter: {store_filtered}")
            
            # Debug: Count after procedure exclusion
            procedure_filtered = Appointment.objects.filter(
                appointment_date__range=(last_2_days, now),
                store_name__in=nps_stores_include_es
            ).exclude(
                procedure_name__in=procedures_es
            ).count()
            logger.info(f"Appointments after procedure exclusion: {procedure_filtered}")
            
            # Debug: Count after status filter
            status_filtered = Appointment.objects.filter(
                appointment_date__range=(last_2_days, now),
                store_name__in=nps_stores_include_es,
                status_label__in=nps_desired_status_es
            ).exclude(
                procedure_name__in=procedures_es
            ).count()
            logger.info(f"Appointments after status filter: {status_filtered}")

            # Optimized query
            appointments = base_query_nps.filter(
                status_label__in=nps_desired_status_es,
                appointment_date__range=(last_2_days, now),
                store_name__in=nps_stores_include_es
            ).order_by('appointment_date')
            
            # Handle distinct
            seen_phones = set()
            unique_appointments = []
            for apt in appointments:
                if apt.customer_phone not in seen_phones:
                    seen_phones.add(apt.customer_phone)
                    unique_appointments.append(apt)
                if len(unique_appointments) >= CONTACTS_TO_LOAD_APT:
                    break
            
            appointments = unique_appointments
            logger.info(f"NPS - Found {len(appointments)} unique appointments")
        
        else:
            logger.warning(f"Unknown contact tag: {contact_tag}")
            return []
        
        # Convert all appointments to contacts using bulk operation
        contacts = convert_appointments_to_contacts_bulk(appointments, contact_tag, user)
        
        # Cache the results
        cache_timeout = 300 if contact_tag == 'NPS' else 3600  # 5 mins for NPS, 1 hour for others
        cache.set(cache_key, contacts, timeout=cache_timeout)
        
        return contacts
        
    except Exception as e:
        logger.error(f"Error processing {contact_tag} appointments: {str(e)}")
        return []