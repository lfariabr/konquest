# tests/apiSocialHub/test_model_file_message.py
import pytest
from apiSocialHub.models.file_message import FileMessage
from django.core.files.uploadedfile import SimpleUploadedFile

#TODO fix this

# @pytest.mark.django_db
# def test_file_message_model_creation():
#     # Create a mock file
#     mock_file = SimpleUploadedFile("test_file.txt", b"Dummy file content.")

#     # Create a FileMessage instance
#     file_message = FileMessage.objects.create(
#         phone="11999999999",
#         message="File message content",
#         file=mock_file,
#         status="Pending",
#     )

#     # Assertions
#     assert file_message.phone == "11999999999"
#     assert file_message.message == "File message content"
#     assert file_message.file.name == "uploads/test_file.txt"
#     assert file_message.status == "Pending"
#     assert str(file_message) == "File Message to 11999999999"


# @pytest.mark.django_db
# def test_file_message_model_update_status():
#     # Create a mock file
#     mock_file = SimpleUploadedFile("test_file.txt", b"Dummy file content.")

#     # Create and update the FileMessage instance
#     file_message = FileMessage.objects.create(
#         phone="11999999999",
#         message="File message content",
#         file=mock_file,
#         status="Pending",
#     )
#     file_message.status = "Failed"
#     file_message.save()

#     # Fetch from DB and assert
#     updated_message = FileMessage.objects.get(id=file_message.id)
#     assert updated_message.status == "Failed"