from django.contrib import admin
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.template.response import TemplateResponse
from dataWrestler.models import ContactAnalytics, MessageAnalytics, ContactAnalyticsForMedia
import json
from django.utils import timezone
from datetime import datetime
import logging
from django.http import HttpResponse, HttpResponseRedirect

logger = logging.getLogger(__name__)

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
    list_display = ('relationship_tag', 'sent_at') # ('message', 'user_phone', 'contact', 'relationship_tag', 'status', 'sent_at')
    list_per_page = 50
    
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        
        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
            
        # Limit to last 3 months by default to improve performance
        three_months_ago = timezone.now() - timezone.timedelta(days=180)
        qs = qs.filter(sent_at__gte=three_months_ago)
            
        # Monthly messages - simplified query
        monthly_data = list(
            qs.annotate(month=TruncMonth('sent_at'))
            .values('month')
            .annotate(total=Count('id'))
            .order_by('month')
        )
        formatted_monthly_data = [
            [x['month'].strftime('%B %Y'), x['total']] for x in monthly_data
        ]
        
        # Tag distribution - limit to top 5
        tag_data = list(
            qs.values('relationship_tag')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        
        # Status distribution - limit to top 5
        status_data = list(
            qs.values('status')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        
        # Phone distribution - limit to top 5
        phone_data = list(
            qs.values('user_phone__phone_number')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        
        as_json = {
            'monthly_data': formatted_monthly_data,
            'tag_data': [[x['relationship_tag'] or 'Unknown', x['total']] for x in tag_data],
            'status_data': [[x['status'] or 'Unknown', x['total']] for x in status_data],
            'phone_data': [[x['user_phone__phone_number'] or 'Unknown', x['total']] for x in phone_data],
        }
        
        response.context_data['chart_data'] = json.dumps(as_json, default=str)
        return response

@admin.register(ContactAnalyticsForMedia)
class ContactAnalyticsForMediaAdmin(admin.ModelAdmin):
    change_list_template = 'admin/contact_analytics_for_media_changelist.html'
    date_hierarchy = 'created_at'
    list_filter = ('store', 'region', 'created_at')
    list_display = ('relationship_tag', 'store', 'region', 'created_at', 'is_lead', 'is_appointment')
    list_per_page = 50
    
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        
        # Use model's queryset directly instead of filtered queryset
        qs = self.model.objects.all()
            
        # Get data for Botox
        botox_data = list(
            qs.filter(relationship_tag='Botox')
            .values('created_at__date')
            .annotate(
                total_contacts=Count('id'),
                total_leads=Count('id', filter=Q(is_lead=True)),
                total_appointments=Count('id', filter=Q(is_appointment=True)),
                total_revenue=(Sum('bill_charge_total_amount', default=0))/100
            )
            .order_by('-created_at__date')  # Most recent first
        )
        
        # Get data for Preenchimento
        preenchimento_data = list(
            qs.filter(relationship_tag='Preenchimento')
            .values('created_at__date')
            .annotate(
                total_contacts=Count('id'),
                total_leads=Count('id', filter=Q(is_lead=True)),
                total_appointments=Count('id', filter=Q(is_appointment=True)),
                total_revenue=(Sum('bill_charge_total_amount', default=0))/100
            )
            .order_by('-created_at__date')  # Most recent first
        )

        instagram_data = list(
            qs.filter(relationship_tag='Instagram')
            .values('created_at__date')
            .annotate(
                total_contacts=Count('id'),
                total_leads=Count('id', filter=Q(is_lead=True)),
                total_appointments=Count('id', filter=Q(is_appointment=True)),
                total_revenue=Sum('bill_charge_total_amount', default=0)
            )
            .order_by('-created_at__date')  # Most recent first
        )
        
        # Format data for template
        def format_data(data):
            return [
                {
                    'date': item['created_at__date'].strftime('%d/%m/%Y'),
                    'total_contacts': item['total_contacts'],
                    'total_leads': item['total_leads'],
                    'total_appointments': item['total_appointments'],
                    'total_revenue': float(item['total_revenue'] or 0),
                }
                for item in data
            ]
        
        # Prepare JSON data
        as_json = {
            'botox_data': format_data(botox_data),
            'preenchimento_data': format_data(preenchimento_data),
            'instagram_data': format_data(instagram_data),
        }
        
        response.context_data['analytics_data'] = json.dumps(as_json, default=str)
        response.context_data['title'] = 'Media Analytics Dashboard'
        
        return response