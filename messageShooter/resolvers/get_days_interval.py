from datetime import timedelta
from apiCrm.models.appointment import Appointment
from django.utils import timezone

today = timezone.now().date()

def calculate_interval(today, appointment_date):
    """
    Calculate days until appointment
    Args:
        today: Current date
        appointment_date: Appointment date
    Returns:
        Number of days until appointment (positive if appointment is in future)
    """
    if isinstance(today, timezone.datetime):
        today = today.date()
    if isinstance(appointment_date, timezone.datetime):
        appointment_date = appointment_date.date()
        
    days_interval = (appointment_date - today).days
    return days_interval