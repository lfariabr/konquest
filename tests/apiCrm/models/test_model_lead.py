from django.db import transaction
from apiCrm.models.lead import Lead
import pytest
from django.db import IntegrityError

@pytest.mark.django_db
def test_lead_model_null_values():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Lead.objects.create(
                id_crm=None,
                name="Test Lead",
                email="test@example",
                phone="1234567890",
                source="source",
                store="store",
                status="active",
                created_at="2024-01-01T00:00:00Z"
            )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Lead.objects.create(
                id_crm="test123",
                name=None,
                email="test@example",
                phone="1234567890",
                source="source",
                store="store",
                status="active",
                created_at="2024-01-01T00:00:00Z"
            )
@pytest.mark.django_db
def test_lead_model_normal_values():
    lead = Lead.objects.create(
        id_crm="test123",
        name="Test Lead",
        email="test@example.com",
        phone="1234567890",
        source="source",
        store="store",
        status="active",
        created_at="2024-01-01T00:00:00Z"
    )

    assert lead.id_crm == "test123"
    assert lead.name == "Test Lead"
    assert lead.email == "test@example.com"
    assert lead.phone == "1234567890"
    assert lead.source == "source"
    assert lead.store == "store"
    assert lead.status == "active"
    assert lead.created_at == "2024-01-01T00:00:00Z"