import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from core.models.message import Message
from core.models.user import User
from core.models.filetype import FileType

@pytest.mark.django_db
def test_message_model():
    user = User.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    message = Message.objects.create(
        user=user,
        title="Test Title",
        text="Test Text")
    assert message.user == user
    assert message.title == "Test Title"
    assert message.text == "Test Text"
    assert message.counter == 0

@pytest.mark.django_db
def test_message_user_required():
    with pytest.raises(IntegrityError):
        Message.objects.create(
            title="Test Title",
            text="Test Text")

@pytest.mark.django_db
def test_message_title_not_blank():
    user = User.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    message = Message(user=user, title="", text="Test Text")
    with pytest.raises(ValidationError):
        message.full_clean()

@pytest.mark.django_db
def test_message_text_not_blank():
    user = User.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    message = Message(user=user, title="Test Title", text="")
    with pytest.raises(ValidationError):
        message.full_clean()

@pytest.mark.django_db
def test_message_counter_default():
    user = User.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    message = Message.objects.create(
        user=user,
        title="Test Title",
        text="Test Text")
    assert message.counter == 0

@pytest.mark.django_db
def test_message_file_null():
    user = User.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    message = Message.objects.create(
        user=user,
        title="Test Title",
        text="Test Text")
    assert message.file.name is None

@pytest.mark.django_db
def test_message_file_type_choices():
    user = User.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    message = Message(user=user, title="Test Title", text="Test Text", file_type="invalid")
    with pytest.raises(ValidationError):
        message.full_clean()

@pytest.mark.django_db
def test_message_file_type_null():
    user = User.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    message = Message.objects.create(
        user=user,
        title="Test Title",
        text="Test Text")
    assert message.file_type is None