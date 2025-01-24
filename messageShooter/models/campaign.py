from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models.userphone import UserPhone
from core.models.user import kUser
from core.models.message import Message  
from core.models.contact import Contact 
from django.core.cache import cache
from django.db import transaction

# Contact Types
CONTACT_TYPE_WHATSAPP = "Whatsapp"
CONTACT_TYPE_APPOINTMENT = "Appointment" #Lead, # BillCharge
CONTACT_TYPE_LEAD = "Lead"
CONTACT_TYPE_BILLCHARGE = "BillCharge"
#TODO adding Leads so we're able to create Queues for interacting with them / Bill charge for follow up activity

CONTACT_TYPES = [
    CONTACT_TYPE_WHATSAPP,
    CONTACT_TYPE_APPOINTMENT,
    CONTACT_TYPE_LEAD,
    CONTACT_TYPE_BILLCHARGE
]

# Contact Tags by Type
CONTACT_TAGS = {
    CONTACT_TYPE_WHATSAPP: ["Preenchimento", "Botox", "Instagram"],
    CONTACT_TYPE_APPOINTMENT: [
                                # Pró-Corpo
                                "Reminder", "Reschedule", "ReminderIpiranga", "ReminderSantoAmaro",
                                "NPS",
                                # "Google My Business",
                                
                                # Plástica
                                "ReschedulePL", "ReminderPL", "VIP"],
    CONTACT_TYPE_LEAD: ["NCC"] # "Verifique seu Blip"],
    # CONTACT_TYPE_BILLCHARGE: ["NCC", "Verifique seu Blip"],
} # "Lead": ["NCC", "Verifique seu Blip"], "BillCharge": ["NCC", "Verifique seu Blip"],

# Campaign Status
STATUS_ACTIVE = "Active"
STATUS_PAUSED = "Paused"
STATUS_COMPLETED = "Completed"

CAMPAIGN_STATUSES = [
    STATUS_ACTIVE,
    STATUS_PAUSED,
    STATUS_COMPLETED,
]

# Campaign Frequencies
FREQUENCY_ONCE = "Once"
FREQUENCY_DAILY = "Daily"
FREQUENCY_WEEKLY = "Weekly"
FREQUENCY_MONTHLY = "Monthly"

CAMPAIGN_FREQUENCIES = [
    (FREQUENCY_ONCE, "Once"),
    (FREQUENCY_DAILY, "Daily"),
    (FREQUENCY_WEEKLY, "Weekly"),
    (FREQUENCY_MONTHLY, "Monthly"),
]

# Constants for days of the week
DAYS_OF_WEEK = [
    ('monday', 'Monday'),
    ('tuesday', 'Tuesday'),
    ('wednesday', 'Wednesday'),
    ('thursday', 'Thursday'),
    ('friday', 'Friday'),
    ('saturday', 'Saturday'),
    ('sunday', 'Sunday'),
]

DAY_NAME_TO_NUMBER = {
    'monday': 0,
    'tuesday': 1,
    'wednesday': 2,
    'thursday': 3,
    'friday': 4,
    'saturday': 5,
    'sunday': 6,
}

DAY_NUMBER_TO_NAME = {v: k for k, v in DAY_NAME_TO_NUMBER.items()}

def validate_active_days(value):
    """Validate that active_days contains valid day names"""
    if not isinstance(value, list):
        raise ValidationError('Active days must be a list')
    
    valid_days = [day[0] for day in DAYS_OF_WEEK]
    invalid_days = [day for day in value if day not in valid_days]
    
    if invalid_days:
        raise ValidationError(
            f'Invalid day names: {", ".join(invalid_days)}. '
            f'Valid options are: {", ".join(valid_days)}'
        )

class Campaign(models.Model):

    # Basic Information
    name = models.CharField(max_length=100)
    contact_type = models.CharField(max_length=100, choices=[(t, t) for t in CONTACT_TYPES])
    contact_tag = models.CharField(max_length=100)
    
    # Contact Relationship
    contacts = models.ManyToManyField(Contact, related_name='campaigns', blank=True)
    
    # Scheduling fields
    frequency = models.CharField(max_length=100, choices=CAMPAIGN_FREQUENCIES, default=FREQUENCY_ONCE)
    execution_time = models.TimeField(
        default='08:00',
        help_text="Time of day when the campaign should run (HH:MM format)"
    )
    active_days = models.JSONField(
        default=list,
        help_text="List of active days (monday, tuesday, etc.)"
    )
    
    # Status
    campaign_status = models.CharField(
        max_length=100, 
        choices=[(s, s) for s in CAMPAIGN_STATUSES],
        default=STATUS_ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)

    # Core data
    userphone = models.ForeignKey(UserPhone, on_delete=models.CASCADE, related_name='campaigns')
    user = models.ForeignKey(kUser, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['frequency', 'campaign_status']),
            models.Index(fields=['contact_type', 'contact_tag']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        """Validate campaign data"""
        # Validate contact_tag based on contact_type
        if self.contact_type and self.contact_tag:
            valid_tags = CONTACT_TAGS.get(self.contact_type, [])
            if self.contact_tag not in valid_tags:
                raise ValidationError({
                    'contact_tag': f'Invalid tag for {self.contact_type}. Valid tags are: {", ".join(valid_tags)}'
                })

        # Validate scheduling data
        if self.frequency != FREQUENCY_ONCE:
            if not self.execution_time:
                raise ValidationError({
                    'execution_time': 'Execution time is required for recurring campaigns'
                })
            
            if not self.active_days:
                raise ValidationError({
                    'active_days': 'At least one active day must be selected for recurring campaigns'
                })

    def save(self, *args, **kwargs):
        """Override save to handle scheduling logic"""
        self.clean()
        
        # Only calculate next_run if:
        # 1. It's not being explicitly set (not in update_fields)
        # 2. It's currently None
        # 3. The campaign is recurring and active
        if (not kwargs.get('update_fields') or ('next_run' not in kwargs.get('update_fields', []))) \
           and self.next_run is None \
           and self.frequency != FREQUENCY_ONCE \
           and self.campaign_status == STATUS_ACTIVE:
            now = timezone.now()
            self.next_run = self.calculate_next_run(now)
        
        super().save(*args, **kwargs)

    def calculate_next_run(self, current_time):
        """Calculate the next run time for a campaign based on its frequency and execution time.

        Args:
            current_time (datetime): The current time to use as a reference.

        Returns:
            datetime: The next run time for the campaign.
        """
        # Get execution time components
        if isinstance(self.execution_time, str):
            execution_hour, execution_minute = map(int, self.execution_time.split(':'))
        else:
            execution_hour = self.execution_time.hour
            execution_minute = self.execution_time.minute
        
        # Get timezone-aware time for today at execution time
        current_tz = current_time.tzinfo
        today_execution = current_time.replace(
            hour=execution_hour,
            minute=execution_minute,
            second=0,
            microsecond=0
        )

        # If current time is before today's execution time, use today
        if current_time < today_execution:
            return today_execution

        # For monthly campaigns, move to 1st of next month
        if self.frequency == FREQUENCY_MONTHLY:
            if current_time.month == 12:
                next_month = 1
                next_year = current_time.year + 1
            else:
                next_month = current_time.month + 1
                next_year = current_time.year
            
            return current_time.replace(
                year=next_year,
                month=next_month,
                day=1,
                hour=execution_hour,
                minute=execution_minute,
                second=0,
                microsecond=0
            )

        # For weekly campaigns, find the next active day
        if self.frequency == FREQUENCY_WEEKLY:
            next_run = today_execution + timezone.timedelta(days=1)
            while next_run.strftime('%A').lower() not in self.active_days:
                next_run += timezone.timedelta(days=1)
            return next_run

        # For daily campaigns, move to next day
        return today_execution + timezone.timedelta(days=1)

    def update_next_run(self):
        """Update the next run time based on current time and frequency"""
        current_time = timezone.now()
        self.next_run = self.calculate_next_run(current_time)
        return self.next_run

    def is_ready_to_run(self):
        """Check if the campaign is ready to run"""
        if self.campaign_status != STATUS_ACTIVE:
            return False
            
        if self.frequency == FREQUENCY_ONCE:
            # Convert execution_time to datetime for today
            now = timezone.now()
            execution_datetime = timezone.datetime.combine(
                now.date(),
                self.execution_time,
                tzinfo=now.tzinfo
            )
            return now >= execution_datetime
            
        # For recurring campaigns, check next_run
        if not self.next_run:
            # If next_run is not set, calculate it
            self.next_run = self.calculate_next_run(timezone.now())
            self.save(update_fields=['next_run'])
            
        return timezone.now() >= self.next_run

    def should_run_today(self):
        """Check if the campaign should run today based on active days"""
        # Get current weekday name
        current_day = DAY_NUMBER_TO_NAME[timezone.now().weekday()]
        
        # Check if today is in active days
        return current_day in self.active_days

    def generate_target_lists(self):
        """
        Generates target lists for this campaign based on current data.
        This should be called each time the campaign runs.
        """
        from messageShooter.models.target_list import TargetList
        from messageShooter.resolvers.get_counter import get_counter_whatsapp
        from core.models.contact import Contact
        
        # Try to get from cache first
        cache_key = f'campaign_contacts_{self.id}'
        contacts = cache.get(cache_key)
        
        if contacts is None:
            # Get eligible contacts based on campaign type
            if self.contact_type == CONTACT_TYPE_WHATSAPP:
                contacts = list(Contact.objects.filter(
                    relationship_tag=self.contact_tag,
                    status='Active'
                ).select_related('userphone'))
                
                # Cache for 1 hour
                cache.set(cache_key, contacts, timeout=3600)
            elif self.contact_type == CONTACT_TYPE_APPOINTMENT:
                from messageShooter.resolvers.get_contacts import get_contact_appointment
                contacts = get_contact_appointment(self.contact_type, self.contact_tag, self.user)
                
                # Cache for 5 minutes for appointments since they're more dynamic
                cache.set(cache_key, contacts, timeout=300)
        
        if not contacts:
            return []

        # Process contacts in batches
        batch_size = 100
        target_lists = []
        
        with transaction.atomic():
            for i in range(0, len(contacts), batch_size):
                batch = contacts[i:i + batch_size]
                
                # Get counter and message once per batch
                counter = get_counter_whatsapp(batch[0].phone, self.contact_tag)
                message = Message.objects.filter(
                    relationship_tag=self.contact_tag,
                    counter=counter
                ).first()
                
                if not message:
                    continue
                
                # Create target lists in bulk
                batch_lists = [
                    TargetList(
                        contact=contact,
                        contact_phone=contact.phone,
                        contact_type=self.contact_type,
                        contact_tag=self.contact_tag,
                        message=message,
                        userphone=self.userphone,
                        status='pending',
                        campaign=self
                    ) for contact in batch
                ]
                
                TargetList.objects.bulk_create(batch_lists)
                target_lists.extend(batch_lists)
        
        return target_lists

    def process_campaign(self):
        """
        Main method to process a campaign run:
        1. Generate new target lists
        2. Create queue items
        3. Update campaign status
        """
        from messageShooter.models.queue import Queue
        
        try:
            # Generate fresh target lists
            target_lists = self.generate_target_lists()
            
            # Create queue items for each target list
            for target_list in target_lists:
                contacts = target_list.get_contacts()
                Queue.objects.create(
                    target_list=target_list,
                    campaign=self,
                    message=target_list.message,
                    userphone=self.userphone,
                    phone_token=self.userphone.phone_token,
                    status='pending',
                    scheduled_time=timezone.now(),
                    total_contacts=len(contacts),
                    processed_contacts={},
                    processed_count=0
                )
            
            # Update campaign status
            self.last_run = timezone.now()
            self.next_run = self.calculate_next_run(self.last_run)
            self.save()
            
            return True, f"Successfully created {len(target_lists)} target lists"
            
        except Exception as e:
            return False, f"Error processing campaign: {str(e)}"