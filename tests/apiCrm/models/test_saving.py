import pytest
from apiCrm.models.lead import Lead
from apiCrm.models.appointment import Appointment
from apiCrm.models.billcharge import BillCharge
from datetime import datetime
import pytz

@pytest.mark.django_db
def test_save_lead_with_valid_data():
    # Arrange: Set up lead data
    lead = Lead(
        id_crm="test123",
        name="Valid Lead",
        email="lead@example.com",
        phone="1234567890",
        source="source",
        store="store",
        status="active",
        created_at="2024-01-01T00:00:00Z"
    )

    # Act: Save the lead
    lead.save()

    # Assert: Lead was saved
    assert Lead.objects.filter(id_crm="test123").exists()

@pytest.mark.django_db
def test_save_lead_with_long_name():
    # Arrange
    long_name = "L" * 101  # Exceeds max length
    lead = Lead(name=long_name)

    # Act & Assert
    with pytest.raises(Exception):  # Expecting a validation error
        lead.save()


@pytest.mark.django_db
def test_save_appointment_with_valid_data():
    # Arrange: Set up appointment data with timezone-aware datetime
    timezone = pytz.UTC
    appointment = Appointment(
        id_crm="apt123",
        status_label="Confirmed",
        store_name="Main Branch",
        customer_id="cust001",
        customer_name="Customer Name",
        customer_phone="1234567890",
        procedure_name="Massage",
        procedure_group="Wellness",
        employee_name="Therapist Name",
        createdby_name="Staff Member",
        createdby_created_at=timezone.localize(datetime(2024, 1, 1, 0, 0, 0)),
        appointment_date=timezone.localize(datetime(2024, 11, 9, 10, 0, 0))
    )

    # Act: Save the appointment
    appointment.save()

    # Assert: Appointment was saved
    assert Appointment.objects.filter(id_crm="apt123").exists()

@pytest.mark.django_db
def test_save_bill_charge_with_valid_data():
    bill_charge = BillCharge(
        quote_id="quote123",
        customer_id="cust001",
        customer_name="John Doe",
        customer_taxvat="123456789",
        customer_email="john.doe@example.com",
        store_name="Main Store",
        total_amount=100.0,
        installments=3,
        paid_at="2024-11-01T10:00:00Z",
        due_at="2024-11-10T10:00:00Z",
        is_paid=True,
        payment_method="Credit Card",
        status="completed",
        quote_items="Service A (Qty: 1, Amount: 100.0)"
    )
    bill_charge.save()
    assert BillCharge.objects.filter(quote_id="quote123").exists()