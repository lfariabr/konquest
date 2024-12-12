# tests/apiSocialHub/test_send_file_message.py
import os
import pytest
import requests
from unittest.mock import patch, MagicMock, mock_open
from apiSocialHub.resolvers.send_file_message import send_file_message

api_url = "https://apinew.socialhub.pro/api/sendMessage"

@patch('os.path.exists', return_value=True)  # Mock file existence check
@patch('builtins.open', new_callable=mock_open, read_data="dummy data")  # Mock file opening
@patch('requests.post')  # Mock the API call

def test_send_file_message_success(mock_post, mock_open_file, mock_exists):
    # Mock API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'success': True,
        'message': 'Message stored successfully. Will be processing in few seconds!'
    }
    mock_post.return_value = mock_response

    # Call the function with test inputs
    response = send_file_message('1234567890', 'Test message', 'dummy_token', 'dummy_path')

    # Assertions
    assert response == {
        'success': True,
        'message': 'Message stored successfully. Will be processing in few seconds!'
    }

    # Validate mocks
    mock_exists.assert_called_once_with('dummy_path')
    mock_open_file.assert_called_once_with('dummy_path', 'rb')
    mock_post.assert_called_once_with(
        api_url,
        data={
            'api_token': 'dummy_token',
            'phone': '1234567890',
            'message': 'Test message',
            'preview_url': True,
        },
        files={'file': ('dummy_path', mock_open_file(), 'application/octet-stream')},
        verify=False,
        timeout=60
    )
@patch('os.path.exists', return_value=True)  # Mock file existence check
@patch('builtins.open', new_callable=mock_open, read_data="dummy data")  # Mock file opening
@patch('requests.post')  # Mock the API call
def test_send_file_message_failed(mock_post, mock_open_file, mock_exists):
    # Mock API response with failure
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_post.return_value = mock_response

    # Call the function with test inputs
    response = send_file_message('1234567890', 'Test message', 'dummy_token', 'dummy_path')

    # Assertions
    assert response == {
        'status': False,
        'error': 'HTTP 400: Bad Request'
    }

    # Validate mocks
    mock_exists.assert_called_once_with('dummy_path')
    mock_open_file.assert_called_once_with('dummy_path', 'rb')
    mock_post.assert_called_once_with(
        api_url,
        data={
            'api_token': 'dummy_token',
            'phone': '1234567890',
            'message': 'Test message',
            'preview_url': True,
        },
        files={'file': ('dummy_path', mock_open_file(), 'application/octet-stream')},
        verify=False,
        timeout=60
    )

@patch('os.path.exists', return_value=True)  # Mock file existence check
@patch('builtins.open', new_callable=mock_open, read_data="dummy data")  # Mock file opening
@patch('requests.post')  # Mock the API call
def test_send_file_message_exception(mock_post, mock_open_file, mock_exists):
    # Simulate a RequestException
    mock_post.side_effect = requests.exceptions.RequestException("Timeout occurred")

    # Call the function with test inputs
    response = send_file_message('1234567890', 'Test message', 'dummy_token', 'dummy_path')

    # Assertions
    assert response == {
        'status': False,
        'error': 'Timeout occurred'
    }

    # Validate mocks
    mock_exists.assert_called_once_with('dummy_path')
    mock_open_file.assert_called_once_with('dummy_path', 'rb')
    mock_post.assert_called_once_with(
        api_url,
        data={
            'api_token': 'dummy_token',
            'phone': '1234567890',
            'message': 'Test message',
            'preview_url': True,
        },
        files={'file': ('dummy_path', mock_open_file(), 'application/octet-stream')},
        verify=False,
        timeout=60
    )

@patch('os.path.exists', return_value=False)  # Mock file existence check to return False
def test_send_file_message_file_not_found(mock_exists):
    # Call the function with test inputs
    response = send_file_message('1234567890', 'Test message', 'dummy_token', 'dummy_path')

    # Assertions
    assert response == {
        'status': False,
        'error': 'File dummy_path not found'
    }

    # Validate mocks
    mock_exists.assert_called_once_with('dummy_path')