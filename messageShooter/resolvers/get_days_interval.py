from datetime import timedelta
from apiCrm.models.appointment import Appointment
from django.utils import timezone

today = timezone.now().date()

def calculate_interval(appointment_created_at):
    """
    Calculate days until appointment
    Args:
        appointment_created_at: Appointment date
    Returns:
        Number of days until appointment (positive if appointment is in future)
    """
    today = timezone.now().date()

    if isinstance(appointment_created_at, timezone.datetime):
        appointment_created_at = appointment_created_at.date()

    days_until_appointment = (appointment_created_at - today).days

    return days_until_appointment
    