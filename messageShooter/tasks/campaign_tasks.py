import logging
import asyncio
from celery import shared_task

# Campaign and Queue
from datetime import timedelta, datetime
from messageShooter.services.scheduler import CampaignScheduler
from messageShooter.services.queue_processor import QueueProcessor

# Organizer
from messageShooter.services.run_organizer import organize_contacts_bulk
from core.models.contact import Contact
from utils.discord import send_discord_message

# python manage.py shell
# from messageShooter.tasks.campaign_tasks import test_organize_contacts
# test_organize_contacts(test_limit=100, test_mode=True)

logger = logging.getLogger(__name__)

@shared_task(
    name='messageShooter.tasks.process_scheduled_campaigns',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
    soft_time_limit=27000  # 450 minutes
)
def process_scheduled_campaigns():
    """
    Periodic task to process campaigns that are scheduled to run.
    This task is scheduled to run every minute to check for campaigns
    that need to be processed.
    """
    logger.info(f"🤖 TASK: Starting to process campaigns @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_message = f"🤖 TASK: Starting to process campaigns @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    send_discord_message(log_message)
    
    campaign_scheduler = CampaignScheduler()
    campaign_scheduler.process_campaigns()

@shared_task(
    name='messageShooter.tasks.process_queues',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
    soft_time_limit=43200  # 12 hours
)
def process_queues():
    """
    Process available message queues.
    """
    logger.info(f"🤖 TASK: Starting to process queues @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_message = f"🤖 TASK: Starting to process queues @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    send_discord_message(log_message)
    queue_processor = QueueProcessor()
    queue_processor.process_queue()

# celery -A konquist call messageShooter.tasks.run_daily_organizer
@shared_task(
    name='messageShooter.tasks.run_daily_organizer',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
    soft_time_limit=3600  # 1 hour
)
def run_daily_organizer(test_mode=False, test_limit=10):
    """
    Run the contact organizer system once daily to update priorities and deduplicate contacts.
    
    This task:
    1. Organizes contacts based on relationship tags
    2. Assigns priorities (1=highest to 3=lowest)
    3. Deduplicates contacts appearing in multiple tag groups
    4. Updates contacts for queue eligibility
    
    Args:
        test_mode (bool): If True, only process a limited number of contacts for testing
        test_limit (int): Number of contacts to process when in test_mode
    
    Returns:
        dict: Statistics about the organization process
    """
    start_time = datetime.now()
    
    # Log mode information
    if test_mode:
        logger.info(f"Starting contact organizer in TEST MODE (limit: {test_limit} contacts) @ {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        logger.info(f"Starting daily contact organizer @ {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        log_message = f"Starting daily contact organizer @ {start_time.strftime('%Y-%m-%d %H:%M:%S')}"
        send_discord_message(log_message)
        
        # Get all active contacts that need organization
        contacts_query = Contact.objects.filter(available_to_queue=True).order_by('-created_at')[:1000]

        # where created_at month/last week...? limitar tamanho do array (memoria da maquina)
        # len do banco de dados
        # e select quantidade das linhas do banco (count) offset limit (0-500, 501-1000, 1001-1500, ...)
        
        # Apply test limit if in test mode
        if test_mode:
            contacts_query = contacts_query[:test_limit]
            logger.info(f"TEST MODE: Limited to {test_limit} contacts")
        
        # Fetch the contacts
        contacts = list(contacts_query)
        total_contacts = len(contacts)
        
        logger.info(f"Found {total_contacts} active contacts to organize")
        
        # Run the organizer
        updated_count = organize_contacts_bulk(contacts)
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Prepare result
        result = {
            'processed_count': total_contacts,
            'updated_count': updated_count,
            'duplicates_removed': total_contacts - updated_count if updated_count < total_contacts else 0,
            'execution_time': execution_time,
            'test_mode': test_mode
        }
        
        # Log detailed results
        logger.info(f"✅ Contact organization completed in {execution_time:.2f} seconds")
        logger.info(f"📊 Organization stats: "
                   f"Processed {result.get('processed_count', 0)} contacts, "
                   f"Updated {result.get('updated_count', 0)} priorities, "
                   f"Removed {result.get('duplicates_removed', 0)} duplicates")
        
        send_discord_message(f"Contact organization completed ✅:\n"
            f"📊 Organization stats: "
            f"Processed {result.get('processed_count', 0)} contacts, "
            f"Updated {result.get('updated_count', 0)} priorities, "
            f"Removed {result.get('duplicates_removed', 0)} duplicates")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in contact organization process: {str(e)}", exc_info=True)
        
        # Create basic result for monitoring
        error_result = {
            'processed_count': 0,
            'error': str(e),
            'execution_time': (datetime.now() - start_time).total_seconds()
        }
        
        # Re-raise for Celery retry mechanism
        raise