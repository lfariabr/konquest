import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from core.models.userphone import UserPhone
from core.models.user import kUser

@pytest.mark.django_db
def test_user_phone_model():
    user = kUser.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    user_phone = UserPhone.objects.create(
        user=user,
        phone_number="1234567890",
        phone_token="test_token",
        phone_description="Test Phone")
    assert user_phone.user == user
    assert user_phone.phone_number == "1234567890"
    assert user_phone.phone_token == "test_token"
    assert user_phone.phone_description == "Test Phone"

@pytest.mark.django_db
def test_user_phone_user_required():
    with pytest.raises(IntegrityError):
        UserPhone.objects.create(
            phone_number="1234567890",
            phone_token="test_token",
            phone_description="Test Phone")

@pytest.mark.django_db
def test_user_phone_phone_number_not_blank():
    user = kUser.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    user_phone = UserPhone(user=user, phone_number="", phone_token="test_token", phone_description="Test Phone")
    with pytest.raises(ValidationError):
        user_phone.full_clean()

@pytest.mark.django_db
def test_user_phone_phone_token_not_blank():
    user = kUser.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    user_phone = UserPhone(user=user, phone_number="1234567890", phone_token="", phone_description="Test Phone")
    with pytest.raises(ValidationError):
        user_phone.full_clean()

@pytest.mark.django_db
def test_user_phone_phone_description_not_blank():
    user = kUser.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    user_phone = UserPhone(user=user, phone_number="1234567890", phone_token="test_token", phone_description="")
    with pytest.raises(ValidationError):
        user_phone.full_clean()

@pytest.mark.django_db
def test_user_phone_created_at_auto_now_add():
    user = kUser.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    user_phone = UserPhone.objects.create(
        user=user,
        phone_number="1234567890",
        phone_token="test_token",
        phone_description="Test Phone")
    assert user_phone.created_at is not None