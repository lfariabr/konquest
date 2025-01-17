import logging
from celery import shared_task
from datetime import timedelta, datetime
from messageShooter.services.scheduler import CampaignScheduler
from messageShooter.services.queue_processor import QueueProcessor
    
logger = logging.getLogger(__name__)

@shared_task(
    name='messageshooter.tasks.process_scheduled_campaigns',
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
    
    campaign_scheduler = CampaignScheduler()
    campaign_scheduler.process_campaigns()
    
    # logger.info(f"Starting to process queues @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    # queue_processor = QueueProcessor()
    # queue_processor.process_queue()

@shared_task(
    name='messageshooter.tasks.process_queues',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
    soft_time_limit=27000  # 450 minutes
)
def process_queues():
    """
    Process available message queues.
    """
    logger.info(f"🤖 TASK: Starting to process queues @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    queue_processor = QueueProcessor()
    queue_processor.process_queue()