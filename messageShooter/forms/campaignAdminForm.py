from django import forms
from django.db.models import Q
from messageShooter.models.campaign import Campaign, DAYS_OF_WEEK
from core.models.message import Message
from django.core.exceptions import ValidationError

class CampaignAdminForm(forms.ModelForm):
    active_days = forms.MultipleChoiceField(
        choices=DAYS_OF_WEEK,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select the days when this campaign should run"
    )
    
    available_messages = forms.CharField(
        widget=forms.Textarea(attrs={'readonly': 'readonly', 'rows': 10}),
        required=False,
        label="Available Messages",
        help_text="Messages that can be used in this campaign based on the selected contact tag"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # # Get unique relationship tags from messages
        # relationship_tags = Message.objects.exclude(
        #     Q(relationship_tag__isnull=True) | Q(relationship_tag='')
        # ).values_list('relationship_tag', flat=True).distinct().order_by('relationship_tag')
        
        # Get relationship tags from CONTACT_TAGS instead of querying the database
        from messageShooter.models.campaign import CONTACT_TAGS
        all_tags = []
        for tags in CONTACT_TAGS.values():
            all_tags.extend(tags)
        
        # Update contact_tag field to only show existing relationship tags
        self.fields['contact_tag'] = forms.ChoiceField(
            choices=[('', '---------')] + [(tag, tag) for tag in sorted(set(all_tags))], # for tag in relationship_tags],
            required=True,
            help_text="Select the tag that determines which messages will be sent"
        )
        
        # Set initial values for active_days if instance exists
        if self.instance.pk and self.instance.active_days:
            self.initial['active_days'] = self.instance.active_days

    def clean_contact_tag(self):
        """Update available messages when contact tag changes"""
        contact_tag = self.cleaned_data.get('contact_tag')
        if contact_tag:
            messages = Message.objects.filter(relationship_tag=contact_tag).order_by('counter')
            if messages.exists():
                data = []
                for msg in messages:
                    preview = msg.text[:50] + '...' if len(msg.text) > 50 else msg.text
                    data.append(f'ID: {msg.id}\nCounter: {msg.counter or "N/A"}\nText: {preview}\n')
                self.data = self.data.copy()  # Make data mutable
                self.data['available_messages'] = '\n'.join(data)
        return contact_tag

    class Meta:
        model = Campaign
        fields = ['name', 'contact_type', 'contact_tag', 'frequency', 'execution_time', 
                 'active_days', 'campaign_status', 'userphone', 'next_run']
        widgets = {
            'next_run': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
