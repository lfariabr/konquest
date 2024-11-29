from django.utils import timezone
from django.db import transaction
from messageShooter.models.queue import Queue
from apiSocialHub.resolvers.send_text_message import send_text_message
from apiSocialHub.resolvers.send_file_message import send_file_message
from core.models.messagelog import MessageLogs
import logging
from django.db.models import Q

logger = logging.getLogger(__name__)

class QueueProcessor:
    max_retries = 3
    base_retry_delay = 5  # Base delay in minutes

    def process_queue(self, batch_size=50):
        """Process pending queue items"""
        logger.info("Starting queue processing")
        
        try:
            now = timezone.now()
            # Get pending messages that are scheduled for now or earlier
            pending_items = Queue.objects.filter(
                Q(status='pending') | Q(status='retrying'),
                scheduled_time__lte=now
            ).select_related('target_list', 'message', 'contact', 'userphone')[:batch_size]
            
            processed_count = 0
            success_count = 0
            error_count = 0
            
            for queue_item in pending_items:
                target = None  # Initialize outside try block
                message = None
                try:
                    with transaction.atomic():
                        # Mark as processing
                        queue_item.status = 'processing'
                        queue_item.save()
                        
                        target = queue_item.target_list
                        message = queue_item.message
                        
                        # Prepare message log entry
                        message_log = MessageLogs(
                            message=message,
                            user=message.user,
                            user_phone=queue_item.userphone,
                            contact=queue_item.contact,
                            status='processing',
                            relationship_tag=target.contact_tag
                        )
                        message_log.save()
                        
                        # Default to text message if no type specified
                        message_type = getattr(message, 'file_type', None)
                        
                        if message_type:
                            success = send_file_message(
                                phone=target.contact_phone,
                                message=message.text,
                                token_socialhub=queue_item.phone_token,
                                file_path=message.file.path if message.file else None
                            )
                        else:
                            success = send_text_message(
                                phone=target.contact_phone,
                                message=message.text,
                                token_socialhub=queue_item.phone_token
                            )
                            
                        if success:
                            queue_item.status = 'sent'
                            queue_item.sent_at = now
                            message_log.status = 'sent'
                            success_count += 1
                        else:
                            # Increment retry count, but don't exceed max retries
                            if queue_item.retry_count < self.max_retries - 1:
                                queue_item.retry_count += 1
                                queue_item.status = 'retrying'
                                # Calculate next retry time with exponential backoff
                                retry_delay = self.base_retry_delay * (2 ** queue_item.retry_count)
                                queue_item.scheduled_time = now + timezone.timedelta(minutes=retry_delay)
                                message_log.status = 'retry'
                            else:
                                # Set to max retries and mark as failed
                                queue_item.retry_count = self.max_retries - 1
                                queue_item.status = 'failed'
                                message_log.status = 'failed'
                            error_count += 1
                            
                        message_log.save()
                        queue_item.save()
                        processed_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing queue item {queue_item.id}: {str(e)}")
                    queue_item.status = 'failed'
                    queue_item.error_message = str(e)
                    queue_item.save()
                    
                    # Only create message log if we have the required objects
                    if message and target:
                        MessageLogs.objects.create(
                            message=message,
                            user=message.user,
                            user_phone=queue_item.userphone,
                            contact=queue_item.contact,
                            status='failed',
                            relationship_tag=target.contact_tag
                        )
                    error_count += 1
            
            logger.info(f"Queue processing complete: {processed_count} processed, {success_count} successful, {error_count} errors")
            return processed_count, success_count, error_count
            
        except Exception as e:
            logger.error(f"Error in queue processing: {str(e)}")
            return 0, 0, 0