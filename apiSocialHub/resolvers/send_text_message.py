# apiSocialHub/resolvers/send_text_message.py
import os
import requests
import json
import logging
from ..logs.logger import send_text_logger

api_url = "https://apinew.socialhub.pro/api/sendMessage"
logger = logging.getLogger(__name__)

def send_text_message(phone, message, token_socialhub, file_path=None):
    phone = str(phone)

    request_data = {
        "api_token": token_socialhub,
        "phone": phone,
        "message": message,
        "preview_url": True
    }
    logger.info(f"Payload: {json.dumps(request_data, indent=2)}")
    logger.info("...")

    headers = {
        "Content-Type": "application/json",
    }

    send_text_logger.info(f"Payload: {json.dumps(request_data, indent=2)}")
    send_text_logger.info("...")

    try:
        response = requests.post(api_url, headers=headers, json=request_data, verify=False, timeout=10)

        if response.status_code == 200:
            data = response.json()
            send_text_logger.info(f"Text message sent to {phone}. Response {data}")
            return data
        else:
            send_text_logger.error(f"Fail to send text message to {phone}. Code: {response.status_code}, Resposta: {response.text}")
            return {"Status": False, "Error": f"HTTP {response.status_code}: {response.text}"}
    
    except requests.exceptions.RequestException as e:
        send_text_logger.error(f"Exception occurred: {str(e)}")
        return {"status": False, "error": str(e)}