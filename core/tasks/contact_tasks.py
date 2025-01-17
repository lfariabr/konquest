from celery import shared_task
from django.db import transaction
import logging
from core.models.contact import Contact

logger = logging.getLogger(__name__)

@shared_task(
    name='core.tasks.check_contacts_in_crm',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
    soft_time_limit=270000  # 45 minutes
)
def check_contacts_in_crm():
    """
    Task to check if contacts exist in CRM tables.
    Processes contacts and tracks progress.
    
    Returns:
        dict: Statistics about the check operation
    """
    logger.info("🤖 TASK: Starting contact check in CRM")
    
    stats = {
        'total_contacts': 0,
        'leads_found': 0,
        'appointments_found': 0,
        'billcharges_found': 0,
        'errors': 0,
        'start_time': timezone.now()
    }
    
    try:
        # Get most recent contacts
        contacts = Contact.objects.exclude(Q(is_lead=True) | Q(is_appointment=True)).order_by('-created_at')[:2000]

        total_contacts = len(contacts)
        stats['total_contacts'] = total_contacts
        
        for idx, contact in enumerate(contacts, 1):
            progress = (idx / total_contacts) * 100
            logger.info(f"Processing contact {idx}/{total_contacts} ({progress:.1f}%) - {contact.phone}")
            
            try:
                with transaction.atomic():
                    # Check if contact exists as lead and update tracking
                    lead = contact.check_if_lead_exists()
                    if lead:
                        stats['leads_found'] += 1
                    
                    # Check if contact exists as appointment and update tracking
                    appointment = contact.check_if_appointment_exists()
                    if appointment:
                        stats['appointments_found'] += 1
                    
                    # Check if contact exists as billcharge and update tracking
                    billcharge = contact.check_if_bill_charges_exists()
                    if billcharge:
                        stats['billcharges_found'] += 1

            except Exception as e:
                stats['errors'] += 1
                logger.error(f"Error processing contact {contact.id}: {str(e)}", exc_info=True)
                continue
        
        # Calculate final statistics
        stats['end_time'] = timezone.now()
        duration = (stats['end_time'] - stats['start_time']).total_seconds()
        
        logger.info(
            "Contact check completed:\n"
            f"- Processed: {stats['total_contacts']} contacts\n"
            f"- Found: {stats['leads_found']} leads, {stats['appointments_found']} appointments, {stats['billcharges_found']} billcharges\n"
            f"- Errors: {stats['errors']}\n"
            f"- Duration: {duration:.2f} seconds"
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to check contacts in CRM: {str(e)}", exc_info=True)
        raise
