from django.db import models
from core.models.userphone import UserPhone
from core.models.message import Message
from apiCrm.models.appointment import Appointment
from core.models.user import kUser

class AppointmentMessageLogs(models.Model):
    """
    Logs for messages sent to appointments
    """
    user = models.ForeignKey(kUser, on_delete=models.CASCADE)
    user_phone = models.ForeignKey(UserPhone, on_delete=models.CASCADE)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    status = models.CharField(max_length=100, default="sent")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Appointment Message Log"
        verbose_name_plural = "Appointment Message Logs"
        ordering = ['-created_at']

    def __str__(self):
        return f"Message log for appointment {self.appointment.id} - {self.status}"