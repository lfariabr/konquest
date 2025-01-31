from celery import shared_task, chain
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
import logging
from typing import Optional
from core.models.contact import Contact
from messageShooter.tasks.campaign_tasks import send_debug_notification

logger = logging.getLogger(__name__)

@shared_task(
    name='core.tasks.check_contacts_in_crm',
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    acks_late=True,
    track_started=True
)
def check_contacts_in_crm(self, batch_size: int = 200, start_id: Optional[int] = None):
    """
    Process contacts in batches to check their CRM status.
    
    Args:
        batch_size: Number of contacts to process in this batch
        start_id: Optional ID to start processing from
    """
    logger.info("Starting contact check in CRM batch%s", f" from ID {start_id}" if start_id else "")
    # log_message = f"🤖 TASK: Starting contact check in core -> lead -> appt -> sales"
    # send_debug_notification(log_message)
    
    stats = {
        'total_contacts': 0,
        'leads_found': 0,
        'appointments_found': 0,
        'billcharges_found': 0,
        'errors': 0,
        'start_time': timezone.now(),
        'last_id': None
    }
    
    try:
        # Build base query
        query = Contact.objects.exclude(Q(is_lead=True) | Q(is_appointment=True))
        
        # Add ID filter if continuing from previous batch
        if start_id:
            query = query.filter(id__lt=start_id)  # Changed from id__gt to id__lt since we're ordering by -id
            
        # Get batch of most recent contacts first
        contacts = query.order_by('-id')[:batch_size]  # Simplified ordering to just -id
        
        if not contacts:
            logger.info("No more contacts to process")
            return stats
            
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
                        
                    # Check bill charges if needed
                    if hasattr(contact, 'needs_bill_charge_check') and hasattr(contact, 'check_if_bill_charge_exists'):
                        if contact.needs_bill_charge_check() and contact.check_if_bill_charge_exists():
                            stats['billcharges_found'] += 1
                            
                stats['last_id'] = contact.id
                    
            except Exception as e:
                stats['errors'] += 1
                logger.error(f"Error processing contact {contact.id}: {str(e)}")
                continue
                
        # If we processed the full batch, schedule the next batch
        if total_contacts == batch_size and stats['last_id']:
            logger.info(f"Scheduling next batch starting from ID {stats['last_id']}")
            check_contacts_in_crm.delay(batch_size=batch_size, start_id=stats['last_id'])
            
        return stats
            
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}")
        if start_id:
            self.retry(
                kwargs={'batch_size': batch_size, 'start_id': start_id},
                countdown=60
            )
        raise

@shared_task(name='core.tasks.trigger_contact_check')
def trigger_contact_check(batch_size: int = 200):
    """
    Trigger the initial contact check batch.
    This is the task that should be scheduled in celery beat.
    """
    logger.info("Triggering contact check process")
    return check_contacts_in_crm.delay(batch_size=batch_size)