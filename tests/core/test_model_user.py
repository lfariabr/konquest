import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from core.models.user import kUser
from django.contrib.auth.hashers import make_password, check_password

@pytest.mark.django_db
def test_user_model():
    user = kUser.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",)
    user.set_password("password")
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.company == "Test Company"
    assert user.check_password("password")

@pytest.mark.django_db
def test_user_email_unique():
    kUser.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="password")
    with pytest.raises(IntegrityError):
        kUser.objects.create(
            name="Another Test User",
            email="test@example.com",
            company="Another Test Company",
            password="another_password")

@pytest.mark.django_db
def test_user_name_not_blank():
    user = kUser(name="", email="test@example.com", company="Test Company")
    with pytest.raises(ValidationError):
        user.full_clean()

@pytest.mark.django_db
def test_user_company_not_blank():
    user = kUser(name="Test User", email="test@example.com", company="")
    with pytest.raises(ValidationError):
        user.full_clean()

@pytest.mark.django_db
def test_user_email_valid_format():
    user = kUser(name="Test User", email="invalid_email", company="Test Company")
    with pytest.raises(ValidationError):
        user.full_clean()

# @pytest.mark.django_db
# def test_user_phone():
#     # First, create a User instance
#     user = kUser.objects.create(
#         name="Test User",
#         email="test@example.com",  # Use a valid email format
#         company="Test Company",
#         password="password")

#     # Now create a UserPhone instance using the User instance
#     user_phone = UserPhone.objects.create(
#         user=user,  # Pass the User instance here
#         phone_number="1234567890",
#         phone_token="token123",
#         phone_description="Test Description"
#     )

#     assert user_phone.user == user  # Check against the user instance, not a string
#     assert user_phone.phone_number == "1234567890"
#     assert user_phone.phone_token == "token123"
#     assert user_phone.phone_description == "Test Description"

# @pytest.mark.django_db
# def test_message_model():
#     # First, create a User instance
#     user = kUser.objects.create(
#         name="Test User",
#         email="test@example.com",  # Use a valid email format
#         company="Test Company",
#         password="password")

#     # Now create a Message instance using the User instance
#     message = Message.objects.create(
#         user=user,  # Pass the User instance here
#         title="Test Title",
#         text="Test Text",
#         file="test.pdf",
#         file_type=FileType.IMAGE
#     )

#     assert message.user == user  # Check against the user instance, not a string
#     assert message.title == "Test Title"
#     assert message.text == "Test Text"
#     assert message.file == "test.pdf"
#     assert message.file_type == FileType.IMAGE

# @pytest.mark.django_db
# def test_message_logs_model():
#     # First, create a User instance
#     user = kUser.objects.create(
#         name="Test User",
#         email="test@example.com",  # Use a valid email format
#         company="Test Company",
#         password="password")

#     # Create a UserPhone instance
#     user_phone = UserPhone.objects.create(
#         user=user,
#         phone_number="1234567890")

#     # Create a Contact instance
#     contact = Contact.objects.create(
#         name="Luis Faria",
#         phone="9876543210",
#         user=user)  # Associate this contact with the User instance

#     # Create a Message instance
#     message = Message.objects.create(
#         user=user,  # Pass the User instance here
#         title="Test Title",
#         text="Test Text",
#         file_type=FileType.IMAGE)

#     # Now create a MessageLogs instance using the Message, User, UserPhone, and Contact instances
#     message_log = MessageLogs.objects.create(
#         message=message,  # Pass the Message instance here
#         user=user,  # Pass the User instance here
#         user_phone=user_phone,  # Pass the UserPhone instance here
#         contact=contact,  # Pass the Contact instance here
#         status="sent")

#     # Check that the MessageLogs instance was created successfully
#     assert message_log.message == message
#     assert message_log.user == user
#     assert message_log.user_phone == user_phone
#     assert message_log.contact == contact
#     assert message_log.status == "sent"
#     assert message_log.sent_at is not None

# @pytest.mark.django_db
# def test_file_type_choices():
#     # Check that the FileType choices are as expected
#     assert FileType.IMAGE == 'image'
#     assert FileType.VIDEO == 'video'
#     assert FileType.AUDIO == 'audio'

#     # Check that the FileType choices are iterable
#     choices = list(FileType)
#     assert len(choices) == 3
#     assert choices[0] == FileType.IMAGE
#     assert choices[1] == FileType.VIDEO
#     assert choices[2] == FileType.AUDIO

# @pytest.mark.django_db
# def test_contact_mdodel():
#     # Create user instance
#     user = kUser.objects.create(
#         name="Test User",
#         email="test@example.com",  # Use a valid email format
#         company="Test Company",
#         password="password"
#     )

#     # Create contact instance
#     contact = Contact.objects.create(
#         name="Luis Faria",
#         phone="9876543210",
#         user=user,
#         relationship_tag="Test Tag",
#         source="Test Source",
#         store="Test Store",
#         region="Test Region",
#         reference_code="Test Code",
#         external_tag="Test Tag"
#     )

#     # Check if the contact was created successfully
#     assert contact.name == "Luis Faria"
#     assert contact.phone == "9876543210"
#     assert contact.user == user
#     assert contact.relationship_tag == "Test Tag"
#     assert contact.source == "Test Source"
#     assert contact.store == "Test Store"
#     assert contact.region == "Test Region"
#     assert contact.reference_code == "Test Code"
#     assert contact.external_tag == "Test Tag"
#     assert contact.created_at is not None