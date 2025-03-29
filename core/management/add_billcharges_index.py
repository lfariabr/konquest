from apiCrm.models.billcharge import BillCharge
from django.db import migrations, models
from django.core.management.base import BaseCommand
import logging

"""
python manage.py create_billcharge_indexes
python manage.py migrate
"""

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Add indexes to BillCharge model"

    def handle(self, *args, **options):
        self.stdout.write("Creating migration for BillCharge indexes...")
        from django.core.management import call_command
        call_command('makemigrations', 'apiCrm', '--name', 'add_billcharge_indexes')
        self.stdout.write(self.style.SUCCESS("Migration created successfully!"))