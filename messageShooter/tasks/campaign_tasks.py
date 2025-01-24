import logging
from celery import shared_task
from datetime import timedelta, datetime
from messageShooter.services.scheduler import CampaignScheduler
from messageShooter.services.queue_processor import QueueProcessor
from apiSocialHub.resolvers.send_text_message import send_text_message

logger = logging.getLogger(__name__)

DEBUG_NOTIFY = {
    'enabled': True,
    'phone': '11963546222',  # Your phone number
    'token': 'rmvYoOnWD5WjcH7Bx5lYTZkGMX2vweN1'  # Your token
}

def send_debug_notification(message):
    """Simple helper to send debug notifications to WhatsApp"""
    if DEBUG_NOTIFY['enabled']:
        try:
            send_text_message(
                DEBUG_NOTIFY['phone'], 
                message,
                DEBUG_NOTIFY['token'],
                None
            )
        except Exception as e:
            logger.error(f"Failed to send debug WhatsApp message: {str(e)}")

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
    send_debug_notification(log_message)
    
    campaign_scheduler = CampaignScheduler()
    campaign_scheduler.process_campaigns()
    
    # logger.info(f"Starting to process queues @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    # queue_processor = QueueProcessor()
    # queue_processor.process_queue()

@shared_task(
    name='messageShooter.tasks.process_queues',
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
    log_message = f"🤖 TASK: Starting to process queues @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    send_debug_notification(log_message)

    queue_processor = QueueProcessor()
    queue_processor.process_queue()