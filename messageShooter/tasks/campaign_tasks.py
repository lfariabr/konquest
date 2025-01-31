import logging
from celery import shared_task
from datetime import timedelta, datetime
from messageShooter.services.scheduler import CampaignScheduler
from messageShooter.services.queue_processor import QueueProcessor
from apiSocialHub.resolvers.send_text_message import send_text_message
import asyncio

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

# @shared_task(
#     name='messageShooter.tasks.process_queues',
#     autoretry_for=(Exception,),
#     retry_kwargs={'max_retries': 3},
#     retry_backoff=True,
#     soft_time_limit=3600,  # 1 hour
#     time_limit=4500   # 75 minutes (hard limit)
# )
# def process_queues(chunk_size: int = 1000, offset: int = 0):
#     """
#     Process available message queues in chunks.
    
#     Args:
#         chunk_size: Number of contacts to process in this chunk
#         offset: Starting offset for contact processing
#     """
#     try:
#         logger.info(f"🤖 TASK: Processing queue chunk, offset={offset}, size={chunk_size} @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
#         log_message = f"🤖 TASK: Processing queue chunk {offset}-{offset+chunk_size}"
#         send_debug_notification(log_message)

#         queue_processor = QueueProcessor()
        
#         # Create event loop and run the async function
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         try:
#             total_contacts, processed = loop.run_until_complete(
#                 queue_processor.process_queue_chunk(chunk_size=chunk_size, offset=offset)
#             )
#         finally:
#             loop.close()
            
#         # If there are more contacts to process, chain the next chunk
#         if total_contacts > (offset + chunk_size):
#             next_offset = offset + chunk_size
#             # Chain the next chunk processing
#             process_queues.apply_async(
#                 args=[chunk_size, next_offset],
#                 countdown=5  # 5 second delay between chunks
#             )
#             logger.info(f"Scheduled next chunk processing starting at offset {next_offset}")
#         else:
#             logger.info("Queue processing completed - no more chunks to process")
            
#         return processed
        
#     except Exception as e:
#         logger.error(f"Error processing queue chunk: {str(e)}", exc_info=True)
#         raise

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
    send_debug_notification(log_message)
    
    # process_queue objects.filter(campaign_nam__"BOTOX")
    # mais 9
    # dispatch
    # count = 0
    # while count < queue_count:
    #   dispatch
    #   count += 200

    queue_processor = QueueProcessor()
    queue_processor.process_queue()