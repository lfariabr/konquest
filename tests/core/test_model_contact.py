import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from core.models.contact import Contact
from core.models.user import User

@pytest.mark.django_db
def test_contact_model():
    user = User.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    contact = Contact.objects.create(
        name="Test Contact",
        phone="1234567890",
        user=user)
    assert contact.name == "Test Contact"
    assert contact.phone == "1234567890"
    assert contact.user == user

@pytest.mark.django_db
def test_contact_name_not_blank():
    user = User.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    contact = Contact(name="", phone="1234567890", user=user)
    with pytest.raises(ValidationError):
        contact.full_clean()

@pytest.mark.django_db
def test_contact_phone_not_blank():
    user = User.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    contact = Contact(name="Test Contact", phone="", user=user)
    with pytest.raises(ValidationError):
        contact.full_clean()

@pytest.mark.django_db
def test_contact_user_required():
    with pytest.raises(IntegrityError):
        Contact.objects.create(
            name="Test Contact",
            phone="1234567890")

@pytest.mark.django_db
def test_contact_default_values():
    user = User.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    contact = Contact.objects.create(
        name="Test Contact",
        phone="1234567890",
        user=user)
    assert contact.relationship_tag == ""
    assert contact.source == "Whatsapp"
    assert contact.store == "CENTRAL"
    assert contact.region == "São Paulo"
    assert contact.external_tag == "SEM TAGS"

@pytest.mark.django_db
def test_contact_reference_code_null():
    user = User.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    contact = Contact.objects.create(
        name="Test Contact",
        phone="1234567890",
        user=user)
    assert contact.reference_code is None