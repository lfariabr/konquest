# apiCrm/tasks.py
from celery import shared_task
from .models import Lead
from datetime import timedelta
from django.utils import timezone

# Worker
@shared_task
def clean_up_leads():
    # threshold_time = timezone.now() - timedelta(minutes=15)
    # deleted_count, _ = Lead.objects.filter(created_at__lt=threshold_time).delete()
    deleted_count, _ = Lead.objects.all().delete()
    print(f"Deleted {deleted_count} leads.")

def fetch_all_leads(start_date, end_date, token):
    pass

def fetch_graphql(session, url, query, variables, token):
    pass

def check_if_lead_is_served():
    pass

def check_if_lead_is_buyer():
    pass

