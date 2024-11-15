# apiSocialHub/resolvers/send_file_message.py
import os
import requests
import json
import logging
from ..logs.logger import send_file_logger

# API URL
api_url = "https://apinew.socialhub.pro/api/sendMessage"
TIMEOUT_SECONDS = 15  # Timeout for API requests

def send_file_message(phone, message, token_socialhub, file_path):
    phone = str(phone)

    request_data = {
        "api_token": token_socialhub,
        "phone": phone,
        "message": message,
        "preview_url": True
    }

    send_file_logger.info(f"Payload: {json.dumps(request_data, indent=2)}")
    send_file_logger.info("Preparing to send file...")

    try:
        # Validate file
        if not os.path.isfile(file_path) or not os.access(file_path, os.R_OK):
            send_file_logger.error(f"File not accessible: {file_path}")
            return {"status": False, "error": f"File not accessible: {file_path}"}

        file_size = os.path.getsize(file_path)
        send_file_logger.info(f"File size: {file_size} bytes")

        # Send file and data
        with open(file_path, 'rb') as file:
            files = {'file': (os.path.basename(file_path), file, 'application/octet-stream')}
            response = requests.post(api_url, files=files, data=request_data, verify=False, timeout=TIMEOUT_SECONDS)

        if response.status_code == 200:
            data = response.json()
            send_file_logger.info(f"File message sent to {phone}. Response: {data}")
            return data
        else:
            send_file_logger.error(f"Failed to send file message to {phone}. Status code: {response.status_code}, Response: {response.text}")
            return {"status": False, "error": f"HTTP {response.status_code}: {response.text}"}
    
    except requests.exceptions.RequestException as e:
        send_file_logger.error(f"RequestException: {type(e).__name__} - {str(e)}")
        return {"status": False, "error": str(e)}