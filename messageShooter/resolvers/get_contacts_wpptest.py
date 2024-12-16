# First, let's check if we have any appointments in the database:

# In Django shell:
from apiCrm.models.appointment import Appointment
from django.utils import timezone
from datetime import timedelta

# Check total appointments
print(f"Total appointments: {Appointment.objects.count()}")

# Check appointments by store
print("\nAppointments by store:")
stores = Appointment.objects.values_list('store_name', flat=True).distinct()
for store in stores:
    count = Appointment.objects.filter(store_name=store).count()
    print(f"- {store}: {count}")

# Check appointments in the last 30 days
now = timezone.now()
thirty_days_ago = now - timedelta(days=30)
recent = Appointment.objects.filter(appointment_date__gte=thirty_days_ago).count()
print(f"\nAppointments in last 30 days: {recent}")

# Check status distribution
print("\nStatus distribution:")
statuses = Appointment.objects.values_list('status_label', flat=True).distinct()
for status in statuses:
    count = Appointment.objects.filter(status_label=status).count()
    print(f"- {status}: {count}")


# Checking our rules
# Check our filter constants
from messageShooter.utils.is_appointment_es import (
    procedures_es,
    stores_include_es,
    reminder_desired_status_es,
    reminder_undesired_status_es
)

print("\nFilter settings:")
print(f"Procedures: {procedures_es}")
print(f"Included stores: {stores_include_es}")
print(f"Reminder desired statuses: {reminder_desired_status_es}")
print(f"Reminder undesired statuses: {reminder_undesired_status_es}")