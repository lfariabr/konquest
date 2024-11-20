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
    contact_type = models.CharField(max_length=100) # choose between "Whatsapp", "Appointment", "Lead", "BillCharge"
    contact_tag = models.CharField(max_length=100) # dictionary according to type    
    
    frequency = models.CharField(max_length=100) # "Once", "Daily", "Weekly", "Monthly"
    start_time = models.DateTimeField() # Option to select "Now"

    campaign_status = models.CharField(max_length=100) # "Active", "Paused", "Completed"
    
    # Core data
    userphone_number = models.ForeignKey(UserPhone, on_delete=models.CASCADE) 
    phone_token = models.ForeignKey(UserPhone, on_delete=models.CASCADE)
    user = models.ForeignKey(kUser, on_delete=models.CASCADE)

    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name