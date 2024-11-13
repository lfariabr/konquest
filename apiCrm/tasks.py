# apiCrm/tasks.py
from celery import shared_task
from apiCrm.models.lead import Lead
from apiCrm.models.appointment import Appointment
from apiCrm.models.billcharge import BillCharge
from datetime import timedelta
from django.utils import timezone

# Worker
@shared_task
def clean_up_leads():
    deleted_count, _ = Lead.objects.all().delete()
    print(f"Deleted {deleted_count} leads.")

@shared_task
def clean_up_appointments():
    deleted_count, _ = Appointment.objects.all().delete()
    print(f"Deleted {deleted_count} appointments.")

@shared_task
def clean_up_bill_charges():
    deleted_count, _ = BillCharge.objects.all().delete()
    print(f"Deleted {deleted_count} bill charges.")

def fetch_all_leads(start_date, end_date, token):
    pass

def fetch_graphql(session, url, query, variables, token):
    pass

def check_if_lead_is_served():
    pass

def check_if_lead_is_buyer():
    pass

