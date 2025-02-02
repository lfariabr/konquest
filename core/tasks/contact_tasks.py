from celery import shared_task, chain
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
import logging
from typing import Optional
from core.models.contact import Contact
from messageShooter.tasks.campaign_tasks import send_debug_notification
from datetime import datetime
from django.core.cache import cache

logger = logging.getLogger(__name__)

@shared_task(
    name='core.tasks.check_contacts_in_crm',
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes between retries
    acks_late=True,
    track_started=True,
    time_limit=3600,      # Hard timeout 1 hour
    soft_time_limit=3000  # Soft timeout 50 minutes
)
def check_contacts_in_crm(self, batch_size: int = 200, start_id: Optional[int] = None):
    """
    Process contacts in batches to check their CRM status.
    Called by trigger_contact_check which is scheduled daily at 1:30 AM.
    
    Args:
        batch_size: Number of contacts to process in this batch
        start_id: Optional ID to start processing from
    """
    lock_id = f"check_contacts_in_crm_lock:{start_id or 'initial'}"
    execution_start = datetime.now()
    
    # Try to acquire lock
    if not cache.add(lock_id, str(execution_start), timeout=3600):  # 1 hour timeout
        logger.warning(f"Task already running for batch {start_id or 'initial'}")
        return None
        
    try:
        logger.info("Starting contact check in CRM batch%s", f" from ID {start_id}" if start_id else "")
        
        stats = {
            'total_contacts': 0,
            'leads_found': 0,
            'appointments_found': 0,
            'billcharges_found': 0,
            'errors': 0,
            'start_time': execution_start,
            'last_id': None
        }
        
        # Build base query
        query = Contact.objects.exclude(Q(is_lead=True) | Q(is_appointment=True))
        
        # Add ID filter if continuing from previous batch
        if start_id:
            query = query.filter(id__gt=start_id)
            
        # Get batch of contacts
        contacts = query.order_by('id')[:batch_size]
        
        if not contacts:
            logger.info("No more contacts to process")
            return stats
            
        total_contacts = len(contacts)
        stats['total_contacts'] = total_contacts
        
        for idx, contact in enumerate(contacts, 1):
            try:
                with transaction.atomic():
                    # Check if contact exists as lead and update tracking
                    if contact.check_if_lead_exists():
                        stats['leads_found'] += 1
                    
                    # Check if contact exists as appointment and update tracking
                    if contact.check_if_appointment_exists():
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
                
        # If we processed the full batch, trigger the next batch
        if total_contacts == batch_size and stats['last_id']:
            # Check if we've hit the safety limit
            total_processed = (start_id or 0) + stats['total_contacts']
            if total_processed >= 1000:
                logger.warning(f"Reached safety limit of 1000 contacts. Processed {total_processed} contacts in total.")
                send_debug_notification(f"⚠️ Contact check stopped: reached 1000 contacts limit. Total processed: {total_processed}")
                return stats
                
            logger.info(f"Triggering next batch starting from ID {stats['last_id']}")
            check_contacts_in_crm.delay(batch_size=batch_size, start_id=stats['last_id'])
            
        return stats
            
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}")
        if self.request.retries < self.max_retries:
            self.retry(
                kwargs={'batch_size': batch_size, 'start_id': start_id},
                countdown=60 * (self.request.retries + 1)  # Progressive backoff
            )
        raise
    finally:
        # Always release the lock
        cache.delete(lock_id)

@shared_task(name='core.tasks.trigger_contact_check')
def trigger_contact_check(batch_size: int = 200):
    """
    Trigger the initial contact check batch.
    This is the task that should be scheduled in celery beat.
    """
    logger.info("Triggering contact check process")
    return check_contacts_in_crm.delay(batch_size=batch_size)