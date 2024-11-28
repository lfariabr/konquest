from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models.userphone import UserPhone
from core.models.user import kUser
from core.models.message import Message  # Import Message model
from core.models.contact import Contact  # Import Contact model

# Contact Types
CONTACT_TYPE_WHATSAPP = "Whatsapp"
CONTACT_TYPE_APPOINTMENT = "Appointment" #Lead, # BillCharge too

CONTACT_TYPES = [
    CONTACT_TYPE_WHATSAPP,
    CONTACT_TYPE_APPOINTMENT,
]

# Contact Tags by Type
CONTACT_TAGS = {
    CONTACT_TYPE_WHATSAPP: ["Preenchimento", "Botox"],
    CONTACT_TYPE_APPOINTMENT: ["Reminder", "Reschedule", "NPS", "Google My Business"],
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
        
        # Calculate next run time only if not using update_fields or if next_run is in update_fields
        if not kwargs.get('update_fields') or 'next_run' in kwargs.get('update_fields', []):
            if self.frequency != FREQUENCY_ONCE and self.campaign_status == STATUS_ACTIVE:
                now = timezone.now()
                self.next_run = self.calculate_next_run(now)
        
        super().save(*args, **kwargs)

    def calculate_next_run(self, from_time):
        """Calculate the next run time based on frequency and active days"""
        # Convert execution_time string to datetime.time if needed
        if isinstance(self.execution_time, str):
            hour, minute = map(int, self.execution_time.split(':'))
            execution_time = timezone.datetime.strptime(f"{hour:02d}:{minute:02d}", "%H:%M").time()
        else:
            execution_time = self.execution_time

        # Start with the base time today
        next_run = timezone.datetime.combine(
            from_time.date(),
            execution_time,
            tzinfo=from_time.tzinfo
        )
        
        # If we're past today's execution time, start from tomorrow
        if from_time > next_run:
            next_run += timezone.timedelta(days=1)
        
        # Convert active_days from names to numbers for comparison
        active_day_numbers = [DAY_NAME_TO_NUMBER[day] for day in self.active_days]
        
        # Find the next active day
        while next_run.weekday() not in active_day_numbers:
            next_run += timezone.timedelta(days=1)
        
        return next_run

    def is_ready_to_run(self):
        """Check if the campaign is ready to run"""
        if self.campaign_status != STATUS_ACTIVE:
            return False
            
        if self.frequency == FREQUENCY_ONCE:
            return timezone.now() >= self.execution_time
            
        return self.next_run and timezone.now() >= self.next_run

    def should_run_today(self):
        """Check if the campaign should run today based on active days"""
        # Get current weekday name
        current_day = DAY_NUMBER_TO_NAME[timezone.now().weekday()]
        
        # Check if today is in active days
        return current_day in self.active_days