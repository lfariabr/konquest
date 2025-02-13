
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
from apiCrm.models.appointment import Appointment
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

def get_reminder_appointment_query(user=None):
    """
    Get appointments eligible for reminders, excluding those with undesired status
    Args:
        user: Optional user to scope the cache key
    Returns:
        QuerySet of appointments for reminders
    """
    now = timezone.now()
    
    # Cache key includes user id if provided
    cache_suffix = f'_{user.id}' if user else ''
    excluded_cache_key = f'excluded_phones_reminder{cache_suffix}'
    excluded_phones = cache.get(excluded_cache_key)

    if excluded_phones is None:
        excluded_phones = set(Appointment.objects.filter(
            status_label__in=reminder_undesired_status_es,  # Atendido, Falta, Reag, Cancel
            store_name__in=reminder_stores_include_es,  # Only check excluded phones from reminder stores
            procedure_name__in=procedures_es,  # Aval
            appointment_date__range=(
                now - timedelta(days=1),  # yesterday
                now + timedelta(days=15)  # next 15 days
            )
        ).values_list('customer_phone', flat=True))
        cache.set(excluded_cache_key, excluded_phones, timeout=3600)

    return Appointment.objects.filter(
        store_name__in=reminder_stores_include_es,  # Only specific stores for reminders
        procedure_name__in=procedures_es,  # Aval
        status_label__in=reminder_desired_status_es,  # Confirmado, Agendado
        appointment_date__range=(
            now,  # Changed from yesterday to now (we don't want past appointments for reminders)
            now + timedelta(days=5)  # next 5 days
        )
    ).exclude(
        customer_phone__in=excluded_phones
    ).order_by('appointment_date')[:CONTACTS_TO_LOAD_APT]  # Changed to ascending order for reminders

# Pró-Corpo ES - Ativo de Falta e Cancelado
def get_reschedule_appointment_query(user=None):
    """
    Get appointments eligible for rescheduling, excluding those with undesired status
    Args:
        user: Optional user to scope the cache key
    Returns:
        QuerySet of appointments
    """
    now = timezone.now()
    
    # Cache key includes user id if provided
    cache_suffix = f'_{user.id}' if user else ''
    excluded_cache_key = f'excluded_phones_reschedule{cache_suffix}'
    excluded_phones = cache.get(excluded_cache_key)

    if excluded_phones is None:
        excluded_phones = set(Appointment.objects.filter(
            status_label__in=reschedule_undesired_status_es,  # Atendido, Agendado, Confirmado
            procedure_name__in=procedures_es,  # Aval
            appointment_date__range=(
                now - timedelta(days=30),
                now + timedelta(days=30)
            )
        ).values_list('customer_phone', flat=True))
        cache.set(excluded_cache_key, excluded_phones, timeout=3600)

    return Appointment.objects.filter(
        store_name__in=stores_include_es_reschedule,  # all stores
        procedure_name__in=procedures_es,  # aval
        status_label__in=reschedule_desired_status_es,  # falta / cancelado
        appointment_date__range=(
            now - timedelta(days=30),
            now - timedelta(days=1)
        )
    ).exclude(
        customer_phone__in=excluded_phones
    ).order_by('-appointment_date')[:CONTACTS_TO_LOAD_APT]
    
def get_nps_appointment_query():
    now = timezone.now()
    
    return Appointment.objects.filter(
        store_name__in=nps_stores_include_es,
        status_label__in=nps_desired_status_es,
        appointment_date__range=(
            now - timedelta(days=2),
            now - timedelta(days=0)
        )
    ).exclude(
        procedure_name__in=procedures_es
    )

def get_reminder_pl_appointment_query(user=None):
    """
    Get appointments eligible for reminders, excluding those with undesired status
    Args:
        user: Optional user to scope the cache key
    Returns:
        QuerySet of appointments for reminders
    """
    now = timezone.now()
    
    # Cache key includes user id if provided
    cache_suffix = f'_{user.id}' if user else ''
    excluded_cache_key = f'excluded_phones_reminder{cache_suffix}'
    excluded_phones = cache.get(excluded_cache_key)

    if excluded_phones is None:
        excluded_phones = set(Appointment.objects.filter(
            status_label__in=reminder_undesired_status_pl,  # Atendido, Falta, Reag, Cancel
            store_name__in=store_include_pl,  # Only check excluded phones from reminder stores
            procedure_name__in=procedures_pl,  # Aval
            appointment_date__range=(
                now - timedelta(days=1),  # yesterday
                now + timedelta(days=15)  # next 15 days
            )
        ).values_list('customer_phone', flat=True))
        cache.set(excluded_cache_key, excluded_phones, timeout=3600)

    return Appointment.objects.filter(
        store_name__in=store_include_pl,  # Only specific stores for reminders
        procedure_name__in=procedures_pl,  # Aval
        status_label__in=reminder_desired_status_pl,  # Confirmado, Agendado
        appointment_date__range=(
            now,  # Changed from yesterday to now (we don't want past appointments for reminders)
            now + timedelta(days=5)  # next 5 days
        )
    ).exclude(
        customer_phone__in=excluded_phones
    ).order_by('appointment_date')[:CONTACTS_TO_LOAD_APT]  # Changed to ascending order for reminders

def get_reschedule_pl_appointment_query(user=None):
    """
    Get appointments eligible for rescheduling, excluding those with undesired status
    Args:
        user: Optional user to scope the cache key
    Returns:
        QuerySet of appointments
    """
    now = timezone.now()
    
    # Cache key includes user id if provided
    cache_suffix = f'_{user.id}' if user else ''
    excluded_cache_key = f'excluded_phones_reschedule{cache_suffix}'
    excluded_phones = cache.get(excluded_cache_key)

    if excluded_phones is None:
        excluded_phones = set(Appointment.objects.filter(
            status_label__in=reschedule_undesired_status_pl,  # Atendido, Agendado, Confirmado
            procedure_name__in=procedures_pl,  # Aval
            appointment_date__range=(
                now - timedelta(days=30),
                now + timedelta(days=30)
            )
        ).values_list('customer_phone', flat=True))
        cache.set(excluded_cache_key, excluded_phones, timeout=3600)

    return Appointment.objects.filter(
        store_name__in=stores_include_pl_reschedule,  # all stores
        procedure_name__in=procedures_pl,  # aval
        status_label__in=reschedule_desired_status_pl,  # falta / cancelado
        appointment_date__range=(
            now - timedelta(days=30),
            now - timedelta(days=1)
        )
    ).exclude(
        customer_phone__in=excluded_phones
    ).order_by('-appointment_date')[:CONTACTS_TO_LOAD_APT]