from datetime import timedelta
from apiCrm.models.appointment import Appointment
from django.utils import timezone

today = timezone.now().date()

def calculate_interval(today, appointment_date):
    days_interval = (today - appointment_date).days
    return days_interval