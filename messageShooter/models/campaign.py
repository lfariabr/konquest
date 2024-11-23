from django.db import models
from core.models.userphone import UserPhone
from core.models.user import kUser

contact_type = ["Whatsapp",
                "Appointment",
                # "Lead",
                # "BillCharge",
]
contact_tag = [{
    "Whatsapp": ["Preenchimento", "Botox"],
    "Appointment": ["Reminder", "Reschedule", "NPS", "Google My Business"],
    # "Lead": ["NCC", "Verifique seu Blip"],
    # "BillCharge": ["NCC", "Verifique seu Blip"],
}]
campaign_status = [
    "Active",
    "Paused",
    "Completed",
]

class Campaign(models.Model):

    name = models.CharField(max_length=100)
    contact_type = models.CharField(max_length=100)  # choose between "Whatsapp", "Appointment", "Lead", "BillCharge"
    contact_tag = models.CharField(max_length=100)  # dictionary according to type    
    
    frequency = models.CharField(max_length=100)  # "Once", "Daily", "Weekly", "Monthly"
    start_time = models.DateTimeField(null=True, blank=True)  # Option to select "Now"

    campaign_status = models.CharField(max_length=100, default="Active")  # "Active", "Paused", "Completed"
    created_at = models.DateTimeField(auto_now_add=True)

    # Core data
    userphone = models.ForeignKey(UserPhone, on_delete=models.CASCADE, related_name='campaigns')
    user = models.ForeignKey(kUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.name