# apiCrm/tasks.py
from django.conf import settings
from decouple import config
from django.db import connection, transaction
from core.models.contact import Contact
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Q
from apiCrm.schemas.resolve_all_data import Query
from apiCrm.schemas.resolve_all_data import fetch_data, process_leads_batch, process_appointments_batch, process_bill_charges_batch
from celery import shared_task
import logging
from django.core.cache import cache


token = config('TOKEN')
logger = logging.getLogger(__name__)

# Are we using these?
from django.db.models import ProtectedError
from apiCrm.models.lead import Lead
from apiCrm.models.appointment import Appointment
from apiCrm.models.billcharge import BillCharge

@shared_task(
    name='apiCrm.cleanup_crm_tables',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
    soft_time_limit=27000 # 450 minutes
)
def cleanup_crm_tables():
    """
    Daily task to clean up CRM-related tables with proper dependency handling.
    Uses PostgreSQL-specific syntax for cleanup while maintaining referential integrity.
    """
    logger.info("Starting CRM tables cleanup")
    
    try:
        with connection.cursor() as cursor:
            # Check if tables exist first
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('apiCrm_billcharge', 'apiCrm_appointment', 'apiCrm_lead')
                );
            """)
            tables_exist = cursor.fetchone()[0]
            
            if not tables_exist:
                logger.warning("One or more CRM tables do not exist. Skipping cleanup.")
                return False
            
            try:
                with transaction.atomic():
                    # Try to clean each table individually to handle partial existence
                    for table in ['apiCrm_billcharge', 'apiCrm_appointment', 'apiCrm_lead']:
                        try:
                            cursor.execute('TRUNCATE TABLE "%s" CASCADE;' % table)
                            logger.info(f"Successfully truncated {table}")
                        except Exception as e:
                            logger.warning(f"Could not truncate {table}: {str(e)}")
                    
                    # Log final table counts
                    cursor.execute("""
                        SELECT 
                            (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'apiCrm_billcharge') as billcharges_exists,
                            (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'apiCrm_appointment') as appointments_exists,
                            (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'apiCrm_lead') as leads_exists;
                    """)
                    counts = cursor.fetchone()
                    logger.info(f"Table existence check: {counts}")
                    
            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}")
                raise
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to clean CRM tables: {str(e)}", exc_info=True)
        raise

@shared_task(
    name='apiCrm.check_contacts_in_crm',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
    soft_time_limit=270000 # 45 minutes
)
def check_contacts_in_crm():
    """
    Task to check if contacts exist in CRM tables.
    Processes contacts and tracks progress.
    
    Returns:
        dict: Statistics about the check operation
    """
    logger.info("Starting contact check in CRM")
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
        # contacts = Contact.objects.all().order_by('-id')[:3000]
        contacts = Contact.objects.exclude(Q(is_lead=True) | Q(is_appointment=True)).order_by('-id')[:50000]

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


@shared_task(
    name='apiCrm.fetch_all_data',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
    soft_time_limit=27000,
    rate_limit='1/h'
)
def fetch_all_data():
    lock_id = "fetch_all_data_lock"
    # Try to acquire lock
    if not cache.add(lock_id, "true", timeout=3600):  # 1 hour timeout
        return "Task already running"
    
    try:
        today = datetime.now().date()
        start_date = (today - timedelta(days=100)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        extended_end_date = (today + timedelta(days=30)).strftime('%Y-%m-%d')

        logger.info(f"Fetching data for dates: {start_date} to {extended_end_date}")
        
        # Fetch raw data using the existing fetch_data function
        leads_data, appointments_data, bill_charges_data = fetch_data(start_date, end_date, extended_end_date, token)
        
        stats = {'processed': 0, 'failed': 0}
        
        # Process each type of data in batches
        leads = process_leads_batch(leads_data, stats, batch_size=1000)
        logger.info(f"Processed {len(leads)} leads. Failed: {stats['failed']}")
        
        appointments = process_appointments_batch(appointments_data, stats, batch_size=1000)
        logger.info(f"Processed {len(appointments)} appointments. Failed: {stats['failed']}")
        
        bill_charges = process_bill_charges_batch(bill_charges_data, stats, batch_size=1000)
        logger.info(f"Processed {len(bill_charges)} bill charges. Failed: {stats['failed']}")
        
        # Return stats
        result_stats = {
            'leads_count': len(leads),
            'appointments_count': len(appointments),
            'bill_charges_count': len(bill_charges),
            'failed_count': stats['failed'],
            'date_range': f"{start_date} to {extended_end_date}"
        }
        
        logger.info(f"Successfully fetched and processed data: {result_stats}")
        return result_stats
        
    except Exception as e:
        logger.error(f"Error in fetch_all_data: {str(e)}", exc_info=True)
        raise
    finally:
        # Release lock
        cache.delete(lock_id)

@shared_task(
    name='apiCrm.process_scheduled_campaigns',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
    soft_time_limit=3600
)
def process_scheduled_campaigns():
    """
    Periodic task to process campaigns that are scheduled to run.
    This task is scheduled to run every minute to check for campaigns
    that need to be processed.
    """
    from messageShooter.services.scheduler import CampaignScheduler
    from messageShooter.services.queue_processor import QueueProcessor
    
    logger.info(f"Starting to process scheduled campaigns @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    campaign_scheduler = CampaignScheduler()
    campaign_scheduler.process_campaigns()
    
    # logger.info(f"Starting to process queues @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    # queue_processor = QueueProcessor()
    # queue_processor.process_queue()

@shared_task(
    name='queue.process_queues',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
    soft_time_limit=3600
)
def process_available_queues():
    from messageShooter.services.queue_processor import QueueProcessor
    logger.info(f"Starting to process queues @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    queue_processor = QueueProcessor()
    queue_processor.process_queue()

@shared_task(
    name='apiCrm.test_redis',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
    soft_time_limit=27000 # 45 minutes
)
def test_redis():
    """Test task to verify Redis connection and Celery worker."""
    logger.info('='*50)
    logger.info('Starting test_redis task')
    try:
        logger.info('Attempting to connect to Redis...')
        # Test Redis cache with multiple operations to keep connection warm
        logger.info('Setting celery_test key...')
        cache.set('celery_test', 'Redis connection working!')
        
        logger.info('Setting celery_heartbeat key...')
        current_time = timezone.now().isoformat()
        cache.set('celery_heartbeat', current_time)
        
        logger.info('Setting celery_counter key...')
        current_counter = cache.get('celery_counter', 0)
        new_counter = current_counter + 1
        cache.set('celery_counter', new_counter)
        
        # Read values back to ensure connection is working both ways
        logger.info('Reading back values...')
        result = cache.get('celery_test')
        heartbeat = cache.get('celery_heartbeat')
        counter = cache.get('celery_counter')
        
        logger.info('='*50)
        logger.info('TEST RESULTS:')
        logger.info(f'Redis test result: {result}')
        logger.info(f'Redis heartbeat: {heartbeat}')
        logger.info(f'Redis counter: {counter}')
        logger.info('='*50)
        
        # Force connection to stay alive with a small pipeline
        logger.info('Testing pipeline operations...')
        cache.set_many({
            'test1': 1,
            'test2': 2,
            'test3': 3
        }, timeout=60)
        
        logger.info('Test completed successfully!')
        logger.info('='*50)
        return True

    except Exception as e:
        logger.error(f'Redis test failed with error: {str(e)}')
        logger.error(f'Error type: {type(e).__name__}')
        # Try to reconnect immediately
        try:
            logger.info('Attempting to reconnect to Redis...')
            cache.close()
            cache.set('celery_reconnect', timezone.now().isoformat())
            logger.info('Redis reconnection successful')
        except Exception as re:
            logger.error(f'Redis reconnection failed with error: {str(re)}')
            logger.error(f'Reconnection error type: {type(re).__name__}')