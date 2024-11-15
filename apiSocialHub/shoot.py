# tests/apiSocialHub/tests.py
import os
from resolvers.send_text_message import send_text_message
from resolvers.send_file_message import send_file_message

# # Test the send_text_message function
# phone = '11963546222'
# message = 'Text message from Konquest Django App'
# token = 'rmvYoOnWD5WjcH7Bx5lYTZkGMX2vweN1'
# file_path = None

# response = send_text_message(phone, message, token, file_path)

# print(response)

## Test the send_file_message function - OK!!
# phone = '11963546222'
# message = 'Test file from Konquest Django App'
# token = 'rmvYoOnWD5WjcH7Bx5lYTZkGMX2vweN1'
# file_path = '/Users/luisfaria/Library/CloudStorage/GoogleDrive-lfariabr@gmail.com/My Drive/LUIS/WORK/18digital/pro-corpo/Lab Programação/dev/_study_python_django/konquist/apiSocialHub/foto-amanda.png'

# if not os.path.exists(file_path):
#     print("Error: File does not exist!")
# else:
#     file_size = os.path.getsize(file_path)
#     print(f"File size: {file_size} bytes")

#     response = send_file_message(phone, message, token, file_path)

#     print("Response:", response)