import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from core.models.messagelog import MessageLogs
from core.models.user import kUser
from core.models.contact import Contact
from core.models.message import Message
from core.models.userphone import UserPhone

@pytest.mark.django_db
def test_message_logs_model():
    user = kUser.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    message = Message.objects.create(
        user=user,
        title="Test Title",
        text="Test Text")
    message_log = MessageLogs.objects.create(
        message=message,
        user=user,
        status="sent")
    assert message_log.message == message
    assert message_log.user == user
    assert message_log.status == "sent"

@pytest.mark.django_db
def test_message_logs_message_required():
    user = kUser.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    with pytest.raises(IntegrityError):
        MessageLogs.objects.create(
            user=user,
            status="sent")

@pytest.mark.django_db
def test_message_logs_user_required():
    user = kUser.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    message = Message.objects.create(
        user=user,
        title="Test Title",
        text="Test Text")
    with pytest.raises(IntegrityError):
        MessageLogs.objects.create(
            message=message,
            status="sent")

@pytest.mark.django_db
def test_message_logs_status_not_blank():
    user = kUser.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    message = Message.objects.create(
        user=user,
        title="Test Title",
        text="Test Text")
    message_log = MessageLogs(message=message, user=user, status="")
    with pytest.raises(ValidationError):
        message_log.full_clean()

@pytest.mark.django_db
def test_message_logs_user_phone_null():
    user = kUser.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    message = Message.objects.create(
        user=user,
        title="Test Title",
        text="Test Text")
    message_log = MessageLogs.objects.create(
        message=message,
        user=user,
        status="sent")
    assert message_log.user_phone is None

@pytest.mark.django_db
def test_message_logs_contact_null():
    user = kUser.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    message = Message.objects.create(
        user=user,
        title="Test Title",
        text="Test Text")
    message_log = MessageLogs.objects.create(
        message=message,
        user=user,
        status="sent")
    assert message_log.contact is None

@pytest.mark.django_db
def test_message_logs_sent_at_auto_now_add():
    user = kUser.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    message = Message.objects.create(
        user=user,
        title="Test Title",
        text="Test Text")
    message_log = MessageLogs.objects.create(
        message=message,
        user=user,
        status="sent")
    assert message_log.sent_at is not None