from django.contrib import admin
from .models.campaign import Campaign
from .models.target_list import TargetList
from .models.queue import Queue
# from .models.job import Job

class TargetListAdmin(admin.ModelAdmin):
    list_display = ('contact_type', 'contact_tag', 'contact_phone', 'reference_id', 'sent_messages_count', 'userphone')
    search_fields = ('contact_type', 'contact_tag', 'contact_phone', 'reference_id')
    list_filter = ('contact_type', 'contact_tag', 'userphone')
    ordering = ('contact_type', 'contact_tag', 'contact_phone')
admin.site.register(TargetList, TargetListAdmin)

class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_type', 'contact_tag', 'frequency', 'start_time', 'campaign_status', 'userphone')
    search_fields = ('name', 'contact_type', 'contact_tag')
    list_filter = ('contact_type', 'contact_tag', 'campaign_status')
    ordering = ('contact_type', 'contact_tag', 'name')
admin.site.register(Campaign, CampaignAdmin)

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