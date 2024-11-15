# tests/apiSocialHub/test_send_text_message.py
import pytest
import requests
from unittest.mock import patch, MagicMock
from apiSocialHub.resolvers.send_text_message import send_text_message
from apiSocialHub.logs.logger import send_text_logger

@patch('requests.post')
def test_send_text_message_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'status': 'success'}
    mock_post.return_value = mock_response
    
    response = send_text_message('phone', 'message', 'token', 'file_path')

    assert response == {'status': 'success'}
    mock_post.assert_called_once_with(
        'https://apinew.socialhub.pro/api/sendMessage',
        headers={'Content-Type': 'application/json'},
        json={
            'api_token': 'token',
            'phone': 'phone',
            'message': 'message',
            'preview_url': True
        },
        verify=False,
        timeout=10
    )

@patch('requests.post')
def test_send_text_message_failure(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = 'Error message'
    mock_post.return_value = mock_response

    response = send_text_message('phone', 'message', 'token', 'file_path')

    assert response == {'Status': False, 'Error': 'HTTP 400: Error message'}
    mock_post.assert_called_once()

@patch('requests.post')
def test_send_text_message_exception(mock_post):
    mock_post.side_effect = requests.exceptions.RequestException('Connection error')

    response = send_text_message('phone', 'message', 'token', 'file_path')

    assert response == {'error': 'Connection error', 'status': False}
    mock_post.assert_called_once()