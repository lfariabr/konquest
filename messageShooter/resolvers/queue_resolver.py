from django.utils import timezone
from messageShooter.models.queue import Queue
from apiSocialHub.resolvers.send_text_message import send_text_message
from apiSocialHub.resolvers.send_file_message import send_file_message
from core.models.messagelog import MessageLogs
from core.models.contact import Contact

def process_queue(batch_size=50):
    """
    Process pending messages in the queue
    :param batch_size: Number of messages to process in one batch
    :return: (processed_count, success_count, error_count)
    """
    now = timezone.now()
    
    # Get pending messages that are scheduled for now or earlier
    pending_messages = Queue.objects.filter(
        status='pending',
        scheduled_time__lte=now
    ).select_related('target_list', 'message', 'contact', 'userphone')[:batch_size]

    processed_count = 0
    success_count = 0
    error_count = 0

    for queue_item in pending_messages:
        try:
            # Mark as processing
            queue_item.status = 'processing'
            queue_item.save()

            # Send the message using appropriate SocialHub sender
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
            message_type = getattr(message, 'message_type', 'text')

            if message_type == 'file':
                success = send_file_message(
                    phone=target.contact_phone,
                    file_url=message.file_url,
                    caption=message.caption,
                    token_socialhub=queue_item.phone_token
                )
            else:  # Default to text message
                success = send_text_message(
                    phone=target.contact_phone,
                    message=message.text,
                    token_socialhub=queue_item.phone_token
                )

            if success:
                queue_item.status = 'completed'
                message_log.status = 'sent'
                success_count += 1
            else:
                if queue_item.retry_count < 3:  # Max 3 retries
                    queue_item.status = 'retrying'
                    queue_item.retry_count += 1
                    queue_item.scheduled_time = now + timezone.timedelta(minutes=5 * queue_item.retry_count)
                    message_log.status = 'retry'
                else:
                    queue_item.status = 'failed'
                    message_log.status = 'failed'
                error_count += 1

            message_log.save()

        except Exception as e:
            queue_item.status = 'failed'
            queue_item.last_error = str(e)
            error_count += 1

            # Log failed message attempt
            MessageLogs.objects.create(
                message=message,
                user=message.user,
                user_phone=queue_item.userphone,
                contact=queue_item.contact,
                status='failed',
                relationship_tag=target.contact_tag
            )

        queue_item.save()
        processed_count += 1

    return processed_count, success_count, error_count