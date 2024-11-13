import pytest
from apiCrm.models.lead import Lead
from apiCrm.models.appointment import Appointment
from apiCrm.models.billcharge import BillCharge
from apiCrm.tasks import clean_up_leads, clean_up_appointments, clean_up_bill_charges
from django.utils import timezone
from celery.result import EagerResult
import logging
from datetime import datetime

@pytest.mark.django_db
def test_clean_up_leads():

    # Use timezone-aware dates
    old_date = timezone.make_aware(timezone.datetime(2023, 1, 1))
    new_date = timezone.make_aware(timezone.datetime(2024, 1, 1))

    Lead.objects.create(name="Old Lead", created_at=old_date)
    Lead.objects.create(name="New Lead", created_at=new_date)

    # Act: Run the cleanup task
    clean_up_leads()

    # Assert: Ensure leads are deleted as expected
    assert Lead.objects.count() == 0

@pytest.mark.django_db
def test_clean_up_appointments():
    # Use timezone-aware dates
    old_date = timezone.make_aware(timezone.datetime(2023, 1, 1))
    new_date = timezone.make_aware(timezone.datetime(2024, 1, 1))

    Appointment.objects.create(store_name="Test Store 1", appointment_date=old_date, createdby_created_at=old_date)
    Appointment.objects.create(store_name="Test Store 2", appointment_date=new_date, createdby_created_at=new_date)

    # Act: Run the cleanup task
    clean_up_appointments()

    # Assert: Ensure appointments are deleted as expected
    assert Appointment.objects.count() == 0

@pytest.mark.django_db
def test_clean_up_bill_charges():
    # Use timezone-aware dates for consistency
    old_date = timezone.make_aware(timezone.datetime(2023, 1, 1))
    new_date = timezone.make_aware(timezone.datetime(2024, 1, 1))

    # Ensure required fields, especially 'is_paid', are provided
    BillCharge.objects.create(
        quote_id="old1",
        paid_at=old_date,
        total_amount=100.0,
        is_paid=True,  # Provide a boolean value for 'is_paid'
        customer_id="cust1",
        customer_name="Old Customer",
        customer_email="old@example.com",
        store_name="Old Store",
        payment_method="Cash",
        status="Completed",
        quote_items="Service A (Qty: 1, Amount: 50.0)"
    )

    BillCharge.objects.create(
        quote_id="new1",
        paid_at=new_date,
        total_amount=150.0,
        is_paid=False,  # Provide a boolean value for 'is_paid'
        customer_id="cust2",
        customer_name="New Customer",
        customer_email="new@example.com",
        store_name="New Store",
        payment_method="Card",
        status="Pending",
        quote_items="Service B (Qty: 2, Amount: 75.0)"
    )

    # Act: Run the cleanup task
    clean_up_bill_charges()

    # Assert: Ensure all bill charges are deleted as expected
    assert BillCharge.objects.count() == 0, "Not all bill charges were deleted."