from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models.userphone import UserPhone
from core.models.user import kUser

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

# Days of Week for Daily Campaigns
DAYS_OF_WEEK = [
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
    (5, "Saturday"),
    (6, "Sunday"),
]

class Campaign(models.Model):

    # Basic Information
    name = models.CharField(max_length=100)
    contact_type = models.CharField(max_length=100, choices=[(t, t) for t in CONTACT_TYPES])
    contact_tag = models.CharField(max_length=100)
    
    # Scheduling
    frequency = models.CharField(max_length=100, choices=CAMPAIGN_FREQUENCIES, default=FREQUENCY_ONCE)
    start_time = models.DateTimeField(null=True, blank=True)
    execution_time = models.TimeField(default='08:00')  # Default to 8 AM, later we can add time | later we can also allow users to set this
    active_days = models.JSONField(default=list, help_text="List of active days (0-6, Monday to Sunday)")
    
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
        
        # Calculate next run time
        if self.frequency != FREQUENCY_ONCE and self.campaign_status == STATUS_ACTIVE:
            now = timezone.now()
            self.next_run = self.calculate_next_run(now)
        
        super().save(*args, **kwargs)

    def calculate_next_run(self, from_time):
        """Calculate the next run time based on frequency and active days"""
        if self.frequency == FREQUENCY_ONCE:
            return self.start_time
        
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
        
        # Find the next active day
        while next_run.weekday() not in self.active_days:
            next_run += timezone.timedelta(days=1)
        
        return next_run

    def is_ready_to_run(self):
        """Check if the campaign is ready to run"""
        if self.campaign_status != STATUS_ACTIVE:
            return False
            
        if self.frequency == FREQUENCY_ONCE:
            return self.start_time and timezone.now() >= self.start_time
            
        return (
            self.next_run and 
            timezone.now() >= self.next_run and 
            timezone.now().weekday() in self.active_days
        )

    def should_run_today(self):
        """Check if the campaign should run today based on active days"""
        # Get current weekday (0 = Monday, 6 = Sunday)
        current_weekday = timezone.now().weekday()
        
        # Check if today is in active days
        return current_weekday in self.active_days