# Easy usage @ terminal
"""
python manage.py clean_leads
"""

from django.core.management.base import BaseCommand
from apiCrm.models.lead import Lead
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Clean leads"

    def handle(self, *args, **options):
        leads = Lead.objects.all()
        
        logger.info(f"Found {len(leads)} leads to clean")

        for lead in leads:
            # Delete all leads
            lead.delete()
                        
        logger.info("Cleaned leads")
        