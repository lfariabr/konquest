from django.contrib import admin
from django.utils import timezone
from .models.campaign import Campaign
from .models.target_list import TargetList
from .models.queue import Queue
# from .models.job import Job
from messageShooter.resolvers.target_list_resolver import create_target_list

class TargetListAdmin(admin.ModelAdmin):
    list_display = ('contact_type', 'contact_tag', 'contact_phone', 'reference_id', 'sent_messages_count', 'userphone') 
    search_fields = ('contact_type', 'contact_tag', 'contact_phone', 'reference_id')
    list_filter = ('contact_type', 'contact_tag', 'userphone')
    ordering = ('contact_type', 'contact_tag', 'contact_phone')
admin.site.register(TargetList, TargetListAdmin)

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_type', 'contact_tag', 'frequency', 'start_time', 'campaign_status', 'userphone', 'next_run']
    search_fields = ('name', 'contact_type', 'contact_tag')
    list_filter = ('contact_type', 'contact_tag', 'campaign_status')
    ordering = ('contact_type', 'contact_tag', 'name')
    actions = ['instant_generate_tlist', 'instant_process_tlist_to_queue']
    
    def instant_generate_tlist(self, request, queryset):
        total_created = 0
        for campaign in queryset:
            # Temporarily override campaign settings for instant run
            original_status = campaign.campaign_status
            original_next_run = campaign.next_run
            original_active_days = campaign.active_days
            original_start_time = campaign.start_time
            
            try:
                # Set up for immediate execution
                now = timezone.now()
                campaign.campaign_status = "Active"
                campaign.next_run = now
                campaign.start_time = now  # Important for FREQUENCY_ONCE campaigns
                campaign.active_days = [now.weekday()]  # Make sure today is an active day
                campaign.save()
                
                # Force refresh from database to ensure changes are applied
                campaign.refresh_from_db()
                
                # Create target list with force_run=True to bypass checks
                created, skipped, errors = create_target_list(campaign.id, force_run=True)
                total_created += created
                
                self.message_user(
                    request,
                    f"Campaign '{campaign.name}': Created {created} targets, Skipped {skipped}, Errors {errors}"
                )
            finally:
                # Restore original campaign settings
                campaign.campaign_status = original_status
                campaign.next_run = original_next_run
                campaign.active_days = original_active_days
                campaign.start_time = original_start_time
                campaign.save()
    
    instant_generate_tlist.short_description = "Instant Generate TList"
    
    def instant_process_tlist_to_queue(self, request, queryset):
        from django.core.management import call_command
        for campaign in queryset:
            try:
                call_command('process_campaign', campaign.contact_tag)
                self.message_user(
                    request,
                    f"Successfully processed campaign '{campaign.name}' target list to queue"
                )
            except Exception as e:
                self.message_user(
                    request,
                    f"Error processing campaign '{campaign.name}': {str(e)}",
                    level='ERROR'
                )
    
    instant_process_tlist_to_queue.short_description = "Instant Process TList to Queue"

class QueueAdmin(admin.ModelAdmin):
    list_display = ('id', 'target_list_id', 'contacts_to_process', 'status', 'priority', 'userphone', 'scheduled_time')
    list_filter = ('status', 'priority', 'userphone')
    search_fields = ('target_list__contact_tag', 'contact__phone', 'userphone__phone_number')
    ordering = ('-priority', 'scheduled_time', 'created_at')

    def contacts_to_process(self, obj):
        """Return count of contacts in the target list"""
        return TargetList.objects.filter(id=obj.target_list.id).count()
    contacts_to_process.short_description = 'Contacts to Process'

admin.site.register(Queue, QueueAdmin)

# admin.site.register(Job)