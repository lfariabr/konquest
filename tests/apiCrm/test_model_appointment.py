from django.db import transaction
from apiCrm.models.appointment import Appointment
import pytest
from django.db import IntegrityError

@pytest.mark.django_db
def test_appointment_model_null_values():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Appointment.objects.create(
                store_name=None,
                appointment_date="2024-01-01T10:00:00Z",
                createdby_created_at="2024-01-01T09:00:00Z"
            )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Appointment.objects.create(
                store_name="Test Store",
                appointment_date=None,
                createdby_created_at="2024-01-01T09:00:00Z"
            )
@pytest.mark.django_db
def test_appointment_model_normal_values():
    appointment = Appointment.objects.create(
        store_name="Test Store",
        appointment_date="2024-01-01T10:00:00Z",
        createdby_created_at="2024-01-01T09:00:00Z"
    )

    assert appointment.store_name == "Test Store"
    assert appointment.appointment_date == "2024-01-01T10:00:00Z"
    assert appointment.createdby_created_at == "2024-01-01T09:00:00Z"