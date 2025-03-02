import logging
from typing import List
from django.db.models import Min, Max, Count
from django.db.models.query import QuerySet
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
from datetime import datetime, timedelta

from core.models.contact import Contact
from apiCrm.models.appointment import Appointment
from messageShooter.resolvers.contactConversor_apt import (
                                                    convert_appointments_to_contacts_bulk)
from messageShooter.utils.is_appointment_es import (
                                                procedures_es, 
                                                stores_exclude_es, 
                                                reminder_stores_include_es, 
                                                intervals_es,
                                                store_include_pl,
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
from konquist.settings import (CONTACTS_TO_LOAD_APT,
                            CONTACTS_TO_LOAD_APT_VIP,
                             CONTACTS_TO_LOAD_APT_VIP_START, 
                             CONTACTS_TO_LOAD_APT_VIP_END)

from messageShooter.helpers.appointment_queries import (
                                                    get_reminder_appointment_query,
                                                    get_reschedule_appointment_query,
                                                    get_reschedule_pl_appointment_query,
                                                    get_reminder_pl_appointment_query,
                                                    get_nps_appointment_query,
                                                    get_vip_query)

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
    
    # Pró-Corpo ES - NPS
    base_query_nps = Appointment.objects.filter(
        store_name__in=nps_stores_include_es
    ).exclude(procedure_name__in=procedures_es)

    # Pró-Corpo ES - VIP
    base_query_vip = Appointment.objects.filter(
        store_name__in=stores_include_es_reschedule,
        status_label__in=nps_desired_status_es
    )
   
    try:
        if contact_tag == 'Reminder':
            reminder_appointments = get_reminder_appointment_query(user)
            appointments = list(reminder_appointments)            
            logger.info(f"Reminder - Found {len(appointments)} appointments for stores {reminder_stores_include_es}")
            
            logger.info("Appointment count per store:")
            store_counts = {}
            for apt in appointments:
                store_counts[apt.store_name] = store_counts.get(apt.store_name, 0) + 1
            for store, count in store_counts.items():
                logger.info(f"  {store}: {count}")
        
        elif contact_tag == 'ReminderPL':
            appointments = get_reminder_pl_appointment_query(user)
            appointments = list(appointments)
            logger.info(f"ReminderPL - Found {len(appointments)} appointments")
        
        elif contact_tag == 'Reschedule':
            reschedule_appointments = get_reschedule_appointment_query(user)
            
            seen_phones = set()
            unique_appointments = []

            for apt in reschedule_appointments:
                if apt.customer_phone not in seen_phones:
                    seen_phones.add(apt.customer_phone)
                    unique_appointments.append(apt)
                if len(unique_appointments) >= CONTACTS_TO_LOAD_APT:
                    break
            
            appointments = unique_appointments
            logger.info(f"Reschedule - Found {len(appointments)} appointments")

        elif contact_tag == 'ReschedulePL':
            reschedule_appointments = get_reschedule_pl_appointment_query(user)

            seen_phones = set()
            unique_appointments = []

            for apt in reschedule_appointments:
                if apt.customer_phone not in seen_phones:
                    seen_phones.add(apt.customer_phone)
                    unique_appointments.append(apt)
                if len(unique_appointments) >= CONTACTS_TO_LOAD_APT:
                    break
            
            appointments = unique_appointments
            logger.info(f"ReschedulePL - Found {len(appointments)} appointments")
        
        elif contact_tag == 'NPS':
            appointments = get_nps_appointment_query()
            
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
        
        elif contact_tag == 'VIP':
            appointments = get_vip_query(user)

            if contact_tag == 'VIP':
                from messageShooter.utils.vip_token_dic import vip_store_dict_info
                
                # Initialize list for all selected appointments
                vip_appointments = []
                
                # Process each store in vip_store_dict_info
                for store_name in vip_store_dict_info.keys():
                    # Get appointments for this store, ensuring uniqueness by customer_phone
                    store_appointments = (
                        appointments.filter(store_name=store_name)
                        .values('customer_phone')
                        .annotate(latest_apt=Max('appointment_date'))
                        .order_by('-latest_apt')
                    )[:100]  # Limit to 100 unique customers
                    # criar uma flag no appointment para apontar se ele foi selecionado no VIP ou não
                    # filtra apenas os selecionados. Desligar a flag depois de ter sido contatado
                    # Luis | Tag: Selecionado VIP | hoje pegar ele
                    # Validar se já é contact com a relationship_tag = VIP
                    
                    # Get the full appointment records - only the latest one per customer
                    phone_numbers = [apt['customer_phone'] for apt in store_appointments]
                    if phone_numbers:
                        store_full_appointments = []
                        for apt in store_appointments:
                            latest = appointments.filter(
                                store_name=store_name,
                                customer_phone=apt['customer_phone'],
                                appointment_date=apt['latest_apt']
                            ).first()
                            if latest:
                                store_full_appointments.append(latest)
                        
                        logger.info(f"Store {store_name}: Found {len(store_appointments)} unique customers, "
                                  f"selected {len(store_full_appointments)} appointments")
                        vip_appointments.extend(store_full_appointments)
                
                appointments = vip_appointments
                logger.info(f"VIP - Final selection: {len(appointments)} unique appointments across "
                          f"{len(vip_store_dict_info)} stores")
                
                # Add detailed breakdown
                store_counts = {}
                for apt in appointments:
                    store_counts[apt.store_name] = store_counts.get(apt.store_name, 0) + 1
                logger.info("Final distribution:")
                for store, count in store_counts.items():
                    logger.info(f"  {store}: {count} appointments")
            
            else:
                # Original logic for non-VIP tags
                seen_phones = set()
                unique_appointments = []
                for apt in appointments:
                    if apt.customer_phone not in seen_phones:
                        seen_phones.add(apt.customer_phone)
                        unique_appointments.append(apt)
                    if len(unique_appointments) >= CONTACTS_TO_LOAD_APT:
                        break
                
                appointments = unique_appointments
                logger.info(f"VIP - Final selection: {len(appointments)} unique appointments")
        
        else:
            logger.warning(f"Unknown contact tag: {contact_tag}")
            return []
        
        # Convert all appointments to contacts using bulk operation
        contacts = convert_appointments_to_contacts_bulk(appointments, contact_tag, user)
        
        # logger.info("TESTING THIS OUT!!)")
        # contacts = []
        
        # Cache the results
        cache_timeout = 300 if contact_tag == 'NPS' else 3600  # 5 mins for NPS, 1 hour for others
        cache.set(cache_key, contacts, timeout=cache_timeout)
        
        return contacts
        
    except Exception as e:
        logger.error(f"Error processing {contact_tag} appointments: {str(e)}")
        return []