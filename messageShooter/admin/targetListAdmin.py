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
    list_per_page = 20
    ordering = ['-created_at']

    def changelist_view(self, request, extra_context=None):
        self.request = request  # Store request if needed for other purposes
        return super().changelist_view(request, extra_context=extra_context)

    def get_queryset(self, request):
        """Override to prefetch related counters in bulk"""
        qs = super().get_queryset(request)
        
        # Get all unique phone numbers and tags
        phones_by_type = {}
        for target in qs:
            if target.contact_phone and target.contact_phone.isdigit():
                phones_by_type.setdefault(target.contact_type, {}).setdefault(target.contact_tag, set()).add(target.contact_phone)
        
        # Bulk fetch counters for each contact type and tag
        from messageShooter.resolvers.get_counter import bulk_get_counter_whatsapp, bulk_get_counter_appointment
        
        # Get or create cache key for this user
        cache_key = f"target_list_counters_{request.user.id}"
        counter_cache = cache.get(cache_key, {})
        
        for contact_type, tags in phones_by_type.items():
            for tag, phones in tags.items():
                logger.info(f"Processing {len(phones)} phones for {contact_type} - {tag}")
                logger.info(f"Sample phones: {list(phones)[:3]}")

                # Determine which counter fetching function to use
                if contact_type.lower() == 'whatsapp':
                    counters = bulk_get_counter_whatsapp(list(phones), tag)
                else:
                    counters = bulk_get_counter_appointment(list(phones), tag)

                # Store results in cache
                for phone, count in counters.items():
                    key = f"{contact_type}:{tag}:{phone}"
                    counter_cache[key] = count
                    logger.info(f"Caching key: {key} = {count}")
        
        # Store in Django's cache for 1 hour
        cache.set(cache_key, counter_cache, 3600)
        logger.info(f"Stored {len(counter_cache)} counters in cache with key {cache_key}")

        return qs

    def get_sent_messages_count(self, obj):
        """Get the number of messages sent to this contact"""
        if not hasattr(self, 'request'):
            logger.error("No request object found")
            return 0
            
        cache_key = f"target_list_counters_{self.request.user.id}"
        counter_cache = cache.get(cache_key, {})
        logger.info(f"Retrieved cache for key {cache_key}. Cache contents: {counter_cache}")
        
        # Construct the same key format used when caching
        key = f"{obj.contact_type}:{obj.contact_tag}:{obj.contact_phone}"
        count = counter_cache.get(key, 0)
        logger.info(f"Looking up key {key} in cache, found count: {count}")
        
        return count
    
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
