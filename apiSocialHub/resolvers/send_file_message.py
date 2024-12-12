# apiSocialHub/resolvers/send_file_message.py
import os
import requests
import json
import logging
from ..logs.logger import send_file_logger
from django.conf import settings

# API URL
api_url = "https://apinew.socialhub.pro/api/sendMessage"
TIMEOUT_SECONDS = 60  # Timeout for API requests

def send_file_message(phone, message, token_socialhub, file_path):
    send_file_logger.info(f"isfile: {os.path.isfile(file_path)}")
    send_file_logger.info(f"access: {os.access(file_path, os.R_OK)}")
    send_file_logger.info(f"getsize: {os.path.getsize(file_path) if os.path.isfile(file_path) else 'N/A'}")

    """
    Send a file message to the specified phone number.
    
    Args:
        phone (str): Phone number of the recipient.
        message (str): Text message to accompany the file.
        token_socialhub (str): API token for authentication.
        file_path (str): Path to the file to be sent.

    Returns:
        dict: Response from the API or error details.
    """
    phone = str(phone)
    request_data = {
        "api_token": token_socialhub,
        "phone": phone,
        "message": message,
        "preview_url": True, 
    }

    send_file_logger.info(f"Payload: {json.dumps(request_data, indent=2)}")
    send_file_logger.info("Preparing to send file...")

    # Check if the file exists
    if not os.path.exists(file_path):
        send_file_logger.error(f"File not found: {file_path}")
        return {"status": False, "error": f"File {file_path} not found"}

     # Prepare file upload
    try:
        with open(file_path, 'rb') as file_content:
            files = {'file': (os.path.basename(file_path), file_content, 'application/octet-stream')}

            # Send the POST request
            response = requests.post(api_url, data=request_data, files=files, verify=False, timeout=TIMEOUT_SECONDS)

            if response.status_code == 200:
                data = response.json()
                send_file_logger.info(f"Message with file sent successfully to {phone}. Response: {data}")
                return data
            else:
                send_file_logger.error(
                    f"Failed to send message with file to {phone}. Status: {response.status_code}, Response: {response.text}"
                )
                return {"status": False, "error": f"HTTP {response.status_code}: {response.text}"}

    except requests.exceptions.RequestException as e:
        send_file_logger.error(f"RequestException: {type(e).__name__} - {str(e)}")
        return {"status": False, "error": str(e)}