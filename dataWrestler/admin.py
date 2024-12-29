from django.contrib import admin
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.template.response import TemplateResponse
from .models import ContactAnalytics, MessageAnalytics
import json

@admin.register(ContactAnalytics)
class ContactAnalyticsAdmin(admin.ModelAdmin):
    change_list_template = 'admin/contact_analytics_changelist.html'
    date_hierarchy = 'created_at'
    list_filter = ('relationship_tag', 'source', 'store', 'region', 'is_lead', 'is_appointment')
    list_display = ('name', 'phone', 'relationship_tag', 'source', 'store', 'region', 'created_at', 'is_lead', 'is_appointment')
    search_fields = ('name', 'phone', 'store', 'region')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        
        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
            
        # Monthly contacts
        monthly_data = list(
            qs.annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(total=Count('id'))
            .order_by('month')
        )
        # Format dates to "Month Year"
        formatted_monthly_data = [
            [x['month'].strftime('%B %Y'), x['total']] for x in monthly_data
        ]
        
        # Tag distribution
        tag_data = list(
            qs.values('relationship_tag')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        
        # Source distribution
        source_data = list(
            qs.values('source')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        
        # Store distribution
        store_data = list(
            qs.values('store')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        
        # Lead and Appointment distribution
        lead_data = list(
            qs.values('is_lead')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        
        appointment_data = list(
            qs.values('is_appointment')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        
        as_json = {
            'monthly_data': formatted_monthly_data, # [[str(x['month']), x['total']] for x in monthly_data],
            'tag_data': [[x['relationship_tag'] or 'Unknown', x['total']] for x in tag_data],
            'source_data': [[x['source'] or 'Unknown', x['total']] for x in source_data],
            'store_data': [[x['store'] or 'Unknown', x['total']] for x in store_data],
            'lead_data': [['Lead' if x['is_lead'] else 'Not Lead', x['total']] for x in lead_data],
            'appointment_data': [['Has Appointment' if x['is_appointment'] else 'No Appointment', x['total']] for x in appointment_data],
        }
        
        response.context_data['chart_data'] = json.dumps(as_json, default=str)
        return response

@admin.register(MessageAnalytics)
class MessageAnalyticsAdmin(admin.ModelAdmin):
    change_list_template = 'admin/message_analytics_changelist.html'
    date_hierarchy = 'sent_at'
    list_filter = ('user_phone', 'relationship_tag', 'status')
    list_display = ('message', 'user_phone', 'contact', 'relationship_tag', 'status', 'sent_at')
    
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        
        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
            
        # Monthly messages
        monthly_data = list(
            qs.annotate(month=TruncMonth('sent_at'))
            .values('month')
            .annotate(total=Count('id'))
            .order_by('month')
        )
        # Format dates to "Month Year"
        formatted_monthly_data = [
            [x['month'].strftime('%B %Y'), x['total']] for x in monthly_data
        ]
        
        # Tag distribution
        tag_data = list(
            qs.values('relationship_tag')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        
        # Status distribution
        status_data = list(
            qs.values('status')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        
        # User phone distribution
        phone_data = list(
            qs.values('user_phone__phone_number')  # Changed from phone to phone_number
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        
        as_json = {
            'monthly_data': formatted_monthly_data, #[[str(x['month']), x['total']] for x in monthly_data],
            'tag_data': [[x['relationship_tag'] or 'Unknown', x['total']] for x in tag_data],
            'status_data': [[x['status'] or 'Unknown', x['total']] for x in status_data],
            'phone_data': [[x['user_phone__phone_number'] or 'Unknown', x['total']] for x in phone_data],  # Changed here too
        }
        
        response.context_data['chart_data'] = json.dumps(as_json, default=str)
        return response