from django.contrib import admin
from core.models.messagelog import MessageLogs
import logging
from django.utils import timezone
from django.core.cache import cache
import json

logger = logging.getLogger(__name__)

class TargetListAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'contact_type',
        'contact_tag', 
        'campaign',
        'contact_phone',
        'get_sent_messages_count',
        'status',
        'created_at',
        'updated_at'
    )
    list_filter = ('contact_type', 'contact_tag', 'campaign', 'status', 'created_at')
    search_fields = ('contact_phone', 'contact_tag', 'campaign__name')
    readonly_fields = ('get_sent_messages_count',)
    actions = ['instant_process_tlist_to_queue']
    list_per_page = 100
    ordering = ['created_at']

    def changelist_view(self, request, extra_context=None):
        """Clear the queryset cache before processing the view"""
        if hasattr(self, '_cached_queryset'):
            del self._cached_queryset
        self.request = request  # Store request if needed for other purposes
        return super().changelist_view(request, extra_context=extra_context)

    def get_queryset(self, request):
        """Override to optimize queryset loading with caching"""
        logger.info("Starting get_queryset in TargetListAdmin")
        
        # Try to get cached queryset for this request
        if hasattr(self, '_cached_queryset'):
            logger.info("Using cached queryset")
            return self._cached_queryset
            
        qs = super().get_queryset(request)
        
        # Add select_related for all foreign key relationships
        qs = qs.select_related(
            'contact',
            'campaign'
        )
        
        # Cache the queryset
        self._cached_queryset = qs
        
        # Add debug logging
        count = qs.count()
        logger.info(f"TargetListAdmin queryset count: {count}")
        
        return qs

    def get_sent_messages_count(self, obj):
        """Get the number of messages sent to this contact using the new counter fields"""
        try:
            if not obj.contact:
                return 0
                
            if obj.contact_tag.lower() == 'botox':
                return obj.contact.botox_messages_sent
            elif obj.contact_tag.lower() == 'preenchimento':
                return obj.contact.preenchimento_messages_sent
            
            return 0
        except Exception as e:
            logger.error(f"Error in get_sent_messages_count: {str(e)}")
            return 0
    
    get_sent_messages_count.short_description = '📨 Sent Messages'

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
                    relationship_tag=first_target.contact_tag,  # This matches what get_message expects
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
