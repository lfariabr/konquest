from django.contrib import admin
from django.urls import path
from django.http import JsonResponse, HttpResponseRedirect
from django.db.models import Q
from messageShooter.forms.campaignAdminForm import CampaignAdminForm
from core.models.message import Message
from messageShooter.resolvers.target_list_resolver import create_target_list
from core.models.user import kUser

class CampaignAdmin(admin.ModelAdmin):
    form = CampaignAdminForm
    change_form_template = 'admin/change_form.html'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "userphone":
            field = super().formfield_for_foreignkey(db_field, request, **kwargs)
            field.label_from_instance = lambda obj: f"{obj.phone_number} ({obj.phone_description})"
            return field
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        urls = [
            path('load-messages/', self.admin_site.admin_view(self.load_messages_view),
                 name='%s_%s_load_messages' % info),
        ]
        return urls + super().get_urls()
    
    def load_messages_view(self, request):
        tag = request.GET.get('tag')
        if tag:
            messages = Message.objects.filter(relationship_tag=tag).order_by('counter')
            data = []
            for msg in messages:
                preview = msg.text[:50] + '...' if len(msg.text) > 50 else msg.text
                data.append(f'ID: {msg.id}\nCounter: {msg.counter or "N/A"}\nText: {preview}\n')
            return JsonResponse({'messages': '\n'.join(data)})
        return JsonResponse({'messages': ''})

    def add_view(self, request, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_load_messages'] = True
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_load_messages'] = True
        return super().change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        if not change:  # Only set the user when creating a new campaign
            obj.user = kUser.objects.get(id=request.user.id)
        super().save_model(request, obj, form, change)

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'contact_type', 'contact_tag', 'userphone')
        }),
        ('Available Messages', {
            'fields': ('available_messages',)
        }),
        ('Scheduling', {
            'fields': ('frequency', 'execution_time', 'active_days')
        }),
        ('Status', {
            'fields': ('campaign_status',)
        }),
    )
    
    list_display = ['name', 'contact_type', 'contact_tag', 'frequency', 'campaign_status', 'last_run', 'next_run']
    list_filter = ['contact_type', 'contact_tag', 'frequency', 'campaign_status']
    search_fields = ['name']
    readonly_fields = ['last_run', 'next_run']
    exclude = ['contacts']
    
    actions = ['instant_generate_tlist']
    
    def get_fieldsets(self, request, obj=None):
        """Customize fieldsets based on whether this is an add or change form"""
        fieldsets = list(self.fieldsets)
        if obj is not None:
            fieldsets.append(
                ('Runtime Information', {
                    'fields': ('last_run', 'next_run'),
                    'classes': ['collapse']
                })
            )
        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        """Customize readonly fields based on whether this is an add or change form"""
        if obj:  # This is an edit form
            return self.readonly_fields
        return []  # This is an add form, no readonly fields

    def instant_generate_tlist(self, request, queryset):
        total_created = 0
        for campaign in queryset:
            try:
                create_target_list(campaign.id, force_run=True)
                total_created += 1
                self.message_user(
                    request,
                    f"Successfully created target list for campaign {campaign.name}",
                    level="success"
                )
            except Exception as e:
                self.message_user(
                    request,
                    f"Error creating target list for campaign {campaign.name}: {str(e)}",
                    level="error"
                )
    instant_generate_tlist.short_description = "🎯 Generate Target List"

    def response_change(self, request, obj):
        if "_load-messages" in request.POST:
            messages = Message.objects.filter(relationship_tag=obj.contact_tag).order_by('counter')
            if messages.exists():
                data = []
                for msg in messages:
                    preview = msg.text[:50] + '...' if len(msg.text) > 50 else msg.text
                    data.append(f'ID: {msg.id}\nCounter: {msg.counter or "N/A"}\nText: {preview}\n')
                obj.available_messages = '\n'.join(data)
                obj.save()
                self.message_user(request, "Messages loaded successfully")
            else:
                self.message_user(request, "No messages found for this tag", level="WARNING")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

    class Media:
        js = ('admin/js/jquery.init.js', 'admin/js/core.js')
