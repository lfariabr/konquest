# tests/apiSocialHub/test_send_file_message.py
import os
import pytest
import requests
from unittest.mock import patch, MagicMock, mock_open
from apiSocialHub.resolvers.send_file_message import send_file_message

@patch('os.path.isfile', return_value=True)  # Mock file existence check
@patch('os.access', return_value=True)  # Mock file accessibility check
@patch('os.path.getsize', return_value=1024)  # Mock file size
@patch('builtins.open', new_callable=mock_open, read_data="dummy data")  # Mock file opening
@patch('requests.post')  # Mock the API call
def test_send_file_message_success(mock_post, mock_open_file, mock_getsize, mock_access, mock_isfile):
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

    # Validate that mocks were called as expected
    mock_isfile.assert_called_once_with('dummy_path')
    mock_access.assert_called_once_with('dummy_path', os.R_OK)
    mock_getsize.assert_called_once_with('dummy_path')
    mock_open_file.assert_called_once_with('dummy_path', 'rb')
    mock_post.assert_called_once_with(
        'https://apinew.socialhub.pro/api/sendMessage',
        files={'file': ('dummy_path', mock_open_file(), 'application/octet-stream')},
        data={
            'api_token': 'dummy_token',
            'phone': '1234567890',
            'message': 'Test message',
            'preview_url': True
        },
        verify=False,
        timeout=15
    )

@patch('os.path.isfile', return_value=True)  # Mock file existence check
@patch('os.access', return_value=True)  # Mock file accessibility check
@patch('os.path.getsize', return_value=1024)  # Mock file size
@patch('builtins.open', new_callable=mock_open, read_data="dummy data")  # Mock file opening
@patch('requests.post')  # Mock the API call
def test_send_file_message_failed(mock_post, mock_open_file, mock_getsize, mock_access, mock_isfile):
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

    # Validate that mocks were called as expected
    mock_isfile.assert_called_once_with('dummy_path')
    mock_access.assert_called_once_with('dummy_path', os.R_OK)
    mock_getsize.assert_called_once_with('dummy_path')
    mock_open_file.assert_called_once_with('dummy_path', 'rb')
    mock_post.assert_called_once_with(
        'https://apinew.socialhub.pro/api/sendMessage',
        files={'file': ('dummy_path', mock_open_file(), 'application/octet-stream')},
        data={
            'api_token': 'dummy_token',
            'phone': '1234567890',
            'message': 'Test message',
            'preview_url': True
        },
        verify=False,
        timeout=15
    )

@patch('os.path.isfile', return_value=True)  # Mock file existence check
@patch('os.access', return_value=True)  # Mock file accessibility check
@patch('os.path.getsize', return_value=1024)  # Mock file size
@patch('builtins.open', new_callable=mock_open, read_data="dummy data")  # Mock file opening
@patch('requests.post')  # Mock the API call
def test_send_file_message_exception(mock_post, mock_open_file, mock_getsize, mock_access, mock_isfile):
    # Simulate a RequestException
    mock_post.side_effect = requests.exceptions.RequestException("Timeout occurred")

    # Call the function with test inputs
    response = send_file_message('1234567890', 'Test message', 'dummy_token', 'dummy_path')

    # Assertions
    assert response == {
        'status': False,
        'error': 'Timeout occurred'
    }

    # Validate that mocks were called as expected
    mock_isfile.assert_called_once_with('dummy_path')
    mock_access.assert_called_once_with('dummy_path', os.R_OK)
    mock_getsize.assert_called_once_with('dummy_path')
    mock_open_file.assert_called_once_with('dummy_path', 'rb')
    mock_post.assert_called_once_with(
        'https://apinew.socialhub.pro/api/sendMessage',
        files={'file': ('dummy_path', mock_open_file(), 'application/octet-stream')},
        data={
            'api_token': 'dummy_token',
            'phone': '1234567890',
            'message': 'Test message',
            'preview_url': True
        },
        verify=False,
        timeout=15
    )