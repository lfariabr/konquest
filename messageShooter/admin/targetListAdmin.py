from django.contrib import admin
from core.models.messagelog import MessageLogs
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

class TargetListAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'contact_type',
        'contact_tag',
        'campaign',
        'contact_phone',
        'sent_messages_count',
        'status',
        'created_at',
        'updated_at'
    )
    list_filter = ('contact_type', 'contact_tag', 'campaign', 'status', 'created_at')
    search_fields = ('contact_phone', 'contact_tag', 'campaign__name')
    readonly_fields = ('sent_messages_count',)
    actions = ['instant_process_tlist_to_queue']

    def sent_messages_count(self, obj):
        """Return next message counter for this contact based on their message logs"""
        # Debug info
        logger.info(f"\n=== Getting next message counter for target list entry ===")
        logger.info(f"Target List: {obj.id}")
        logger.info(f"Phone: {obj.contact_phone}")
        logger.info(f"Tag: {obj.contact_tag}")
        
        if not obj.contact:
            logger.info("No contact associated with target list entry")
            return 0
            
        logger.info(f"Contact: id={obj.contact.id}, phone={obj.contact.phone}, tag={obj.contact.relationship_tag}")
        
        # Get the last sent message for this contact and tag
        last_message = MessageLogs.objects.filter(
            contact=obj.contact,
            relationship_tag=obj.contact_tag,  # Filter by tag
            status='sent'
        ).order_by('-sent_at').first()
        
        # If no messages sent yet, start with counter 0
        if not last_message:
            logger.info(f"No messages sent yet for contact {obj.contact.id}")
            return 0
            
        # Get the counter of the last message and add 1
        next_counter = last_message.message.counter + 1 if last_message.message else 0
        logger.info(f"Last message counter was {next_counter - 1}, next counter will be {next_counter}")
        
        return next_counter
    sent_messages_count.short_description = '📨 Sent Messages'

    def instant_process_tlist_to_queue(self, request, queryset):
        """Directly add selected target lists to the queue"""
        from messageShooter.models.queue import Queue
        from messageShooter.resolvers.get_userphone import get_userphone
        from messageShooter.resolvers.get_message import get_message
        from messageShooter.resolvers.get_counter import get_counter_whatsapp
        from itertools import groupby
        from operator import attrgetter
        
        success_count = 0
        error_count = 0
        
        # Group target lists by campaign
        sorted_targets = sorted(queryset, key=attrgetter('campaign_id'))
        for campaign_id, campaign_targets in groupby(sorted_targets, key=attrgetter('campaign_id')):
            try:
                campaign_targets = list(campaign_targets)  # Convert iterator to list
                if not campaign_targets:
                    continue
                
                first_target = campaign_targets[0]
                
                # Get userphone for this tag
                userphone, phone_token = get_userphone(first_target.contact_tag)
                if not userphone:
                    self.message_user(
                        request,
                        f"No userphone found for tag {first_target.contact_tag}",
                        level='WARNING'
                    )
                    continue
                
                # Get first contact's counter and message
                counter = get_counter_whatsapp(first_target.contact_phone, first_target.contact_tag)
                initial_message = get_message(
                    contact_type=first_target.contact_type,
                    contact_tag=first_target.contact_tag,
                    counter=counter
                )
                if not initial_message:
                    self.message_user(
                        request,
                        f"No message found for counter {counter} and tag {first_target.contact_tag}",
                        level='WARNING'
                    )
                    continue
                
                # Create one queue for all target lists in this campaign
                queue = Queue.objects.create(
                    target_list=first_target,  # Use first target list as reference
                    message=initial_message,  # Set message based on first contact's counter
                    userphone=userphone,
                    phone_token=phone_token,
                    status='pending',
                    scheduled_time=timezone.now(),
                    total_contacts=len(campaign_targets),  # Total contacts is number of target lists
                    processed_contacts={},
                    processed_count=0
                )
                success_count += 1
                
                # Update all target lists' status
                for target in campaign_targets:
                    target.status = 'processing'
                    target.save()
                
                # Log queue creation
                logger.info(f"Queue created for campaign {first_target.campaign}:")
                logger.info(f"- Campaign: {first_target.campaign}")
                logger.info(f"- Contact Tag: {first_target.contact_tag}")
                logger.info(f"- Total Target Lists: {len(campaign_targets)}")
                logger.info(f"- Initial Message: {initial_message.id} (counter={counter})")
                
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Error adding campaign {campaign_id} to queue: {str(e)}",
                    level='ERROR'
                )
        
        if success_count > 0:
            self.message_user(
                request,
                f"Successfully added {success_count} campaign(s) to queue",
                level='SUCCESS'
            )
        
        if error_count > 0:
            self.message_user(
                request,
                f"Failed to add {error_count} campaign(s) to queue",
                level='WARNING'
            )

    instant_process_tlist_to_queue.short_description = "🔄 Add to Queue"
