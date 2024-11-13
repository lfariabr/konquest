from django.db import transaction
from apiCrm.models.billcharge import BillCharge
import pytest
from django.db import IntegrityError

@pytest.mark.django_db
def test_bill_charge_model_normal_values():
    bill_charge = BillCharge.objects.create(
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

    assert bill_charge.quote_id == "quote123"
    assert bill_charge.customer_id == "cust001"
    assert bill_charge.customer_name == "John Doe"
    assert bill_charge.customer_taxvat == "123456789"
    assert bill_charge.customer_email == "john.doe@example.com"
    assert bill_charge.store_name == "Main Store"
    assert bill_charge.total_amount == 100.0
    assert bill_charge.installments == 3
    assert bill_charge.paid_at == "2024-11-01T10:00:00Z"
    assert bill_charge.due_at == "2024-11-10T10:00:00Z"
    assert bill_charge.is_paid == True
    assert bill_charge.payment_method == "Credit Card"
    assert bill_charge.status == "completed"
    assert bill_charge.quote_items == "Service A (Qty: 1, Amount: 100.0)"

    @pytest.mark.django_db
    def test_bill_charge_model_null_values():
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                BillCharge.objects.create(
                    quote_id=None,
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
    
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                BillCharge.objects.create(
                    quote_id="quote123",
                    customer_id=None,
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