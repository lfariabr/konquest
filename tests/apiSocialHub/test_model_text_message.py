# tests/apiSocialHub/test_model_text_message.py
import pytest
from apiSocialHub.models.text_message import TextMessage

@pytest.mark.django_db
def test_text_message_model_creation():
    # Create a TextMessage instance
    text_message = TextMessage.objects.create(
        phone="11999999999",
        message="Test message content",
        status="Pending",
    )

    # Assertions
    assert text_message.phone == "11999999999"
    assert text_message.message == "Test message content"
    assert text_message.status == "Pending"
    assert str(text_message) == "Text Message to 11999999999"


@pytest.mark.django_db
def test_text_message_model_update_status():
    # Create and update the TextMessage instance
    text_message = TextMessage.objects.create(
        phone="11999999999",
        message="Test message content",
        status="Pending",
    )
    text_message.status = "Sent"
    text_message.save()

    # Fetch from DB and assert
    updated_message = TextMessage.objects.get(id=text_message.id)
    assert updated_message.status == "Sent"