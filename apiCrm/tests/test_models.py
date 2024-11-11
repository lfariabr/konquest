import pytest
from apiCrm.models import Lead, Appointment, BillCharge

@pytest.mark.django_db
def test_lead_model():
    lead = Lead.objects.create(
        id_crm="test123",
        name="Test Lead",
        email="test@example",
        phone="1234567890",
        source="source",
        store="store",
        status="active",
        created_at="2024-01-01T00:00:00Z"
    )

    assert lead.id_crm == "test123"
    assert lead.name == "Test Lead"
    assert Lead.objects.count() == 1

@pytest.mark.django_db
def test_appointment_model():
    appointment = Appointment.objects.create(
        store_name="Test Store",
        appointment_date="2024-01-01T10:00:00Z",
        createdby_created_at="2024-01-01T09:00:00Z"
    )

    assert appointment.store_name == "Test Store"
    assert appointment.appointment_date == "2024-01-01T10:00:00Z"
    assert Appointment.objects.count() == 1

@pytest.mark.django_db
def test_create_bill_charge():
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