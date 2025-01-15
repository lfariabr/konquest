from django.contrib import admin
from core.models.messagelog import MessageLogs
import logging
from django.utils import timezone
from django.core.cache import cache
import json
from messageShooter.resolvers.get_counter import get_counter_appointment
from messageShooter.resolvers.get_counter import get_counter_whatsapp


logger = logging.getLogger(__name__)

class TargetListAdmin(admin.ModelAdmin):
    # Optimize list display and filters
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
    list_filter = ('contact_type', 'contact_tag', 'status')
    search_fields = ('contact_phone', 'contact_tag', 'campaign__name')
    list_select_related = ('campaign', 'contact')
    ordering = ('-created_at',)  # Most recent first
    list_per_page = 50  # Reduce items per page for faster loading
    actions = ['instant_process_tlist_to_queue']
    readonly_fields = ('get_sent_messages_count',)
    
    def get_queryset(self, request):
        """
        Optimize queryset loading with select_related and filtering.
        """
        logger.info("Starting get_queryset in TargetListAdmin")
        
        # Store request for use in other methods
        self.request = request
        
        # Build optimized queryset with all needed relations and fields
        qs = super().get_queryset(request)
        qs = qs.select_related(
            'contact',
            'campaign'
        ).only(
            'id',
            'contact_type',
            'contact_tag',
            'campaign__id',
            'campaign__name',
            'contact_phone',
            'status',
            'created_at',
            'updated_at',
            'contact__id',
            'contact__phone',
            'contact__botox_messages_sent',
            'contact__preenchimento_messages_sent',
            'contact__appointment_created_at'
        )
        
        # Log query stats
        count = qs.count()
        logger.info(f"TargetListAdmin queryset count: {count}")
        
        return qs
        
    def get_search_results(self, request, queryset, search_term):
        """Optimize search by using indexed fields"""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        
        # If there's a search term, ensure we're still using our optimizations
        if search_term:
            queryset = queryset.select_related(
                'contact',
                'campaign'
            ).only(
                'id',
                'contact_type',
                'contact_tag',
                'campaign__id',
                'campaign__name',
                'contact_phone',
                'status',
                'created_at',
                'updated_at'
            )
        
        return queryset, use_distinct
        
    def changelist_view(self, request, extra_context=None):
        """Optimize changelist view"""
        # Add any additional context needed
        if extra_context is None:
            extra_context = {}
            
        # Get basic stats for the header
        total_count = self.get_queryset(request).count()
        extra_context['total_targets'] = total_count
        
        response = super().changelist_view(request, extra_context)
        return response
        
    def get_sent_messages_count(self, obj):
        """Get the number of messages sent to this contact with caching"""
        if not obj.contact:
            return 0
            
        # Generate cache key for the specific contact and tag
        cache_key = f'sent_msg_count:{obj.contact.id}:{obj.contact_type}:{obj.contact_tag}'
        
        try:
            # Try to get from cache first
            count = cache.get(cache_key)
            if count is not None:
                return count
                
            # Calculate count based on contact type
            if obj.contact_type == 'Whatsapp':
                if obj.contact_tag.lower() == 'botox':
                    count = obj.contact.botox_messages_sent
                elif obj.contact_tag.lower() == 'preenchimento':
                    count = obj.contact.preenchimento_messages_sent
                else:
                    count = 0
                    
            elif obj.contact_type == 'Appointment':
                if obj.contact_tag in ["NPS", "Reschedule", "ReschedulePL"]:
                    count = get_counter_whatsapp(obj.contact.phone, obj.contact_tag)
                elif obj.contact_tag in ["Reminder", "ReminderPL"]:
                    from messageShooter.resolvers.get_days_interval import calculate_interval
                    if obj.contact.appointment_created_at:
                        count = calculate_interval(obj.contact.appointment_created_at)
                    else:
                        count = 0
            
            elif obj.contact_type == 'Lead':
                if obj.contact_tag in ["NCC"]:
                    count = get_counter_whatsapp(obj.contact.phone, obj.contact_tag)

                else:
                    count = 0
                    
            # Cache the result with appropriate timeout
            timeout = 3600 if obj.contact_type == 'Whatsapp' else 300
            cache.set(cache_key, count, timeout=timeout)
            
            return count
            
        except Exception as e:
            logger.error(f"Error in get_sent_messages_count for contact {obj.contact.id}: {str(e)}")
            return 0
            
    def instant_process_tlist_to_queue(self, request, queryset):
        """Efficiently process target lists to queue with bulk operations"""
        from messageShooter.models.queue import Queue
        from messageShooter.resolvers.get_userphone import get_userphone
        from messageShooter.resolvers.get_message import get_message
        from messageShooter.resolvers.get_counter import get_counter_whatsapp
        from django.db import transaction
        from itertools import groupby
        from operator import attrgetter
        import time
        
        start_time = time.time()
        success_count = 0
        error_count = 0
        
        # Pre-fetch userphones for all unique tags
        unique_tags = set(queryset.values_list('contact_tag', flat=True))
        userphones = {
            tag: get_userphone(tag) 
            for tag in unique_tags
        }
        
        # Group target lists by campaign for efficient processing
        sorted_targets = sorted(queryset, key=attrgetter('campaign_id'))
        
        with transaction.atomic():
            for campaign_id, campaign_targets in groupby(sorted_targets, key=attrgetter('campaign_id')):
                try:
                    campaign_targets = list(campaign_targets)
                    if not campaign_targets:
                        continue
                        
                    first_target = campaign_targets[0]
                    userphone, phone_token = userphones.get(first_target.contact_tag, (None, None))
                    
                    if not userphone:
                        self.message_user(
                            request,
                            f"No userphone found for tag {first_target.contact_tag}",
                            level='WARNING'
                        )
                        continue
                        
                    # Get message efficiently
                    counter = get_counter_whatsapp(first_target.contact_phone, first_target.contact_tag)
                    initial_message = get_message(
                        contact_type=first_target.contact_type,
                        relationship_tag=first_target.contact_tag,
                        counter=counter
                    )
                    
                    if not initial_message:
                        self.message_user(
                            request,
                            f"No message found for counter {counter} and tag {first_target.contact_tag}",
                            level='WARNING'
                        )
                        continue
                        
                    # Create queue and update target lists in bulk
                    queue = Queue.objects.create(
                        target_list=first_target,
                        message=initial_message,
                        userphone=userphone,
                        phone_token=phone_token,
                        status='pending',
                        scheduled_time=timezone.now(),
                        total_contacts=len(campaign_targets),
                        processed_contacts={},
                        processed_count=0
                    )
                    
                    # Bulk update target lists
                    target_ids = [t.id for t in campaign_targets]
                    from messageShooter.models.target_list import TargetList
                    TargetList.objects.filter(id__in=target_ids).update(status='processing')
                    
                    success_count += 1
                    
                    # Detailed logging
                    logger.info(
                        f"Queue created for campaign {first_target.campaign}:\n"
                        f"- Campaign: {first_target.campaign}\n"
                        f"- Contact Tag: {first_target.contact_tag}\n"
                        f"- Total Target Lists: {len(campaign_targets)}\n"
                        f"- Initial Message: {initial_message.id} (counter={counter})"
                    )
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing campaign {campaign_id}: {str(e)}")
                    self.message_user(request, f"Error adding campaign {campaign_id} to queue: {str(e)}", level='ERROR')
        
        # Log performance metrics
        execution_time = time.time() - start_time
        logger.info(f"Queue processing completed in {execution_time:.2f}s: {success_count} successes, {error_count} errors")
        
        if success_count > 0:
            self.message_user(request, f"Successfully added {success_count} campaign(s) to queue", level='SUCCESS')
        if error_count > 0:
            self.message_user(request, f"Failed to add {error_count} campaign(s) to queue", level='WARNING')
            
    get_sent_messages_count.short_description = '📨 Sent Messages'

    instant_process_tlist_to_queue.short_description = "🔄 Add to Queue"
