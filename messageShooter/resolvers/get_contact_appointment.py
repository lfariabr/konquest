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
    
    # Pró-Corpo ES - Confirmação
    base_query_reminder = Appointment.objects.filter(
        store_name__in=reminder_stores_include_es,
        procedure_name__in=procedures_es,
        status_label__in=reminder_desired_status_es
    )

    # Pró-Corpo ES - Ativo de Falta e Cancelado
    base_query_reschedule = Appointment.objects.filter(
        store_name__in=stores_include_es_reschedule,
        procedure_name__in=procedures_es,
        status_label__in=reschedule_desired_status_es
    )

    # Pró-Corpo ES - NPS
    base_query_nps = Appointment.objects.filter(
        store_name__in=nps_stores_include_es
    ).exclude(procedure_name__in=procedures_es)

    # Pró-Corpo ES - VIP
    base_query_vip = Appointment.objects.filter(
        store_name__in=stores_include_es_reschedule,
        status_label__in=nps_desired_status_es
    )

    # Mais Cirurgia - Confirmação
    base_query_reminder_pl = Appointment.objects.filter(
        store_name__in=store_include_pl,
        procedure_name__in=procedures_pl,
        status_label__in=reminder_desired_status_pl
    )

    # Mais Cirurgia - Ativo de Falta e Cancelado
    base_query_reschedule_pl = Appointment.objects.filter(
        store_name__in=stores_include_pl_reschedule,
        procedure_name__in=procedures_pl,
        status_label__in=reschedule_desired_status_pl
    )
   
    try:
        if contact_tag == 'Reminder':
            five_days_future = now + timedelta(days=5)
            one_day_past = now - timedelta(days=1)
            thirty_days_future = now + timedelta(days=30)
            
            # Get excluded phones first (can be cached)
            excluded_cache_key = f'excluded_phones_reminder_{user.id}'
            excluded_phones = cache.get(excluded_cache_key)
            
            if excluded_phones is None:
                excluded_phones = set(Appointment.objects.filter(
                    status_label__in=reminder_undesired_status_es,
                    procedure_name__in=procedures_es,
                    appointment_date__range=(one_day_past, thirty_days_future)
                ).values_list('customer_phone', flat=True))
                cache.set(excluded_cache_key, excluded_phones, timeout=3600)
            
            # Get appointments with optimized query
            # Maybe we can add date_range in the original base_query_reminder 
            # and use here simply to exclude the set of excluded phones
            reminder_appointments = base_query_reminder.filter(
                appointment_date__range=(now, five_days_future)
            ).exclude(
                customer_phone__in=excluded_phones
            ).order_by('appointment_date')[:CONTACTS_TO_LOAD_APT]

            appointments = list(reminder_appointments)            
            logger.info(f"Reminder - Found {len(appointments)} appointments for stores {reminder_stores_include_es}")
            
            logger.info("Appointment count per store:")
            store_counts = {}
            for apt in appointments:
                store_counts[apt.store_name] = store_counts.get(apt.store_name, 0) + 1
            for store, count in store_counts.items():
                logger.info(f"  {store}: {count}")
        
        elif contact_tag == 'ReminderPL':
            five_days_future = now + timedelta(days=5)
            one_day_past = now - timedelta(days=1)
            thirty_days_future = now + timedelta(days=30)

            # Get excluded phones first (can be cached)
            excluded_cache_key = f'excluded_phones_reminder_pl_{user.id}'
            excluded_phones = cache.get(excluded_cache_key)
            
            if excluded_phones is None:
                excluded_phones = set(Appointment.objects.filter(
                    status_label__in=reminder_undesired_status_pl,
                    procedure_name__in=procedures_pl,
                    appointment_date__range=(one_day_past, thirty_days_future)
                ).values_list('customer_phone', flat=True))
                cache.set(excluded_cache_key, excluded_phones, timeout=3600)
            
            # Get appointments with optimized query
            appointments = base_query_reminder_pl.filter(
                appointment_date__range=(now, five_days_future),
            ).exclude(
                customer_phone__in=excluded_phones
            ).order_by('appointment_date')[:CONTACTS_TO_LOAD_APT]
            
            appointments = list(appointments)
            logger.info(f"ReminderPL - Found {len(appointments)} appointments")
        
        elif contact_tag == 'Reschedule':
            thirty_days_past = now - timedelta(days=30)
            thirty_days_future = now + timedelta(days=30)
            last_7_days = now - timedelta(days=7)
            
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
            reschedule_appointments = base_query_reschedule.filter(
                appointment_date__gte=last_7_days
            ).exclude(
                customer_phone__in=excluded_phones
            ).order_by('-appointment_date')
            
            # Handle distinct in Python for better compatibility
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
            thirty_days_past = now - timedelta(days=30)
            thirty_days_future = now + timedelta(days=30)

            # Get excluded phones (cached)
            excluded_cache_key = f'excluded_phones_reschedule_pl_{user.id}'
            excluded_phones = cache.get(excluded_cache_key)
            
            if excluded_phones is None:
                excluded_phones = set(Appointment.objects.filter(
                    status_label__in=reschedule_undesired_status_pl,
                    procedure_name__in=procedures_pl,
                    appointment_date__range=(thirty_days_past, thirty_days_future)
                ).values_list('customer_phone', flat=True))
                cache.set(excluded_cache_key, excluded_phones, timeout=3600)
            
            # Optimized query with distinct handling
            reschedule_appointments = base_query_reschedule_pl.filter(
            ).exclude(
                customer_phone__in=excluded_phones
            ).order_by('-appointment_date')
            
            # Handle distinct in Python for better compatibility
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
        
        elif contact_tag == 'VIP':
            # 1. Get October appointments
            month_october_start = datetime(2024, 10, 1)
            month_october_end = datetime(2024, 10, 31, 23, 59, 59)

            # Debug store filtering
            logger.info(f"Filtering on these stores: {stores_include_es_reschedule}")
            
            # Get distribution of appointments by store
            store_distribution = base_query_vip.filter(
                appointment_date__range=(month_october_start, month_october_end),
                status_label__in=nps_desired_status_es
            ).values('store_name').annotate(count=Count('id')).order_by('-count')
            
            logger.info("Store distribution before filtering:")
            for store in store_distribution:
                logger.info(f"  {store['store_name']}: {store['count']} appointments")

            october_appointments = base_query_vip.filter(
                appointment_date__range=(month_october_start, month_october_end),
                store_name__in=stores_include_es_reschedule,
                status_label__in=nps_desired_status_es
            )
            
            october_phones = set(october_appointments.values_list('customer_phone', flat=True))
            logger.info(f"Found {october_appointments.count()} appointments in October ({len(october_phones)} unique customers)")
            
            # 2. Get November onwards appointments
            month_november_start = datetime(2024, 11, 1)
            yesterday = now - timedelta(days=1)

            november_onwards_appointments = base_query_vip.filter(
                appointment_date__range=(month_november_start, yesterday),
                store_name__in=stores_include_es_reschedule,
                status_label__in=nps_desired_status_es
            )
            
            november_onwards_phones = set(
                november_onwards_appointments.values_list('customer_phone', flat=True)
            )
            
            # Calculate retention
            returning_customers = october_phones.intersection(november_onwards_phones)
            logger.info(f"Found {november_onwards_appointments.count()} appointments from November onwards ({len(november_onwards_phones)} unique customers)")
            logger.info(f"Retention analysis: {len(returning_customers)} out of {len(october_phones)} October customers returned in November+")

            # # Sample of loyal customers (returned in November+)
            # logger.info("\nSample of 5 loyal customers who returned:")
            # loyal_sample = october_appointments.filter(
            #     customer_phone__in=list(returning_customers)
            # ).values('customer_phone', 'store_name', 'appointment_date', 'status_label')[:5]
            
            # for apt in loyal_sample:
            #     # Get their November+ appointment
            #     future_apt = november_onwards_appointments.filter(
            #         customer_phone=apt['customer_phone']
            #     ).values('appointment_date', 'store_name').first()
                
            #     logger.info(f"  Customer {apt['customer_phone']}:")
            #     logger.info(f"    October visit: {apt['store_name']} on {apt['appointment_date']}")
            #     logger.info(f"    Returned: {future_apt['store_name']} on {future_apt['appointment_date']}")

            # 3. Filter October appointments to exclude phones that appear in November onwards
            appointments = october_appointments.exclude(
                customer_phone__in=november_onwards_phones
            ).order_by('appointment_date')
            
            logger.info(f"After filtering, found {appointments.count()} October appointments without subsequent visits")

            if contact_tag == 'VIP':
                from messageShooter.utils.vip_token_dic import vip_store_dict_info
                
                # Initialize list for all selected appointments
                vip_appointments = []
                
                logger.info(f"Starting VIP contact selection, targeting 10 contacts per store")
                
                # Process each store in vip_store_dict_info
                for store_name in vip_store_dict_info.keys():
                    # Get appointments for this store, ensuring uniqueness by customer_phone
                    store_appointments = (
                        appointments.filter(store_name=store_name)
                        .values('customer_phone')
                        .annotate(latest_apt=Max('appointment_date'))
                        .order_by('-latest_apt')
                    )[:100]  # Limit to 100 unique customers
                    #TODO: think about this logic
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