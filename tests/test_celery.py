import pytest
from unittest.mock import Mock, patch, call
from django.db import connection
from celery.signals import task_prerun, task_postrun, after_task_publish
from celery import signals
import logging
from konquist.celery import (
    app,
    task_prerun_handler,
    task_postrun_handler,
    task_sent_handler,
    setup_celery_logging,
    task_success_handler,
    task_failure_handler
)

@pytest.fixture
def mock_celery_app():
    with patch('konquist.celery.app') as mock_app:
        mock_app.conf = Mock()
        yield mock_app

@pytest.fixture
def mock_logger():
    with patch('konquist.celery.logger') as mock_log:
        yield mock_log

@pytest.fixture
def mock_connection(mocker):
    """Mock database connection."""
    mock = mocker.patch('konquist.celery.connection')
    mock.close = mocker.Mock()
    return mock

def test_celery_app_configuration(mock_celery_app):
    """Test basic Celery app configuration settings."""
    # Verify broker settings
    assert app.conf.broker_url == 'redis://:nofuckingdaysoff@localhost:6379/0'
    
    # Check basic app settings
    assert app.conf.task_serializer == 'json'
    assert app.conf.result_serializer == 'json'
    assert app.conf.accept_content == ('json',)  
    assert app.conf.timezone == 'America/Sao_Paulo'
    assert app.conf.enable_utc is False

def test_celery_beat_schedule(mock_celery_app):
    """Test Celery beat schedule configuration."""
    beat_schedule = app.conf.beat_schedule
    
    # Verify scheduled tasks exist
    assert 'test_redis_connection' in beat_schedule
    
    # Check specific task configuration
    task_config = beat_schedule['test_redis_connection']
    assert task_config['task'] == 'apiCrm.tasks.test_redis'
    assert 'schedule' in task_config  

def test_task_prerun_handler(mock_logger, mock_connection):
    """Test pre-task execution handling."""
    task = Mock()
    task.name = 'test_task'
    task_id = 'test-id-123'
    
    task_prerun_handler(task_id=task_id, task=task, args=(), kwargs={})
    
    # Verify logging and connection handling
    mock_logger.info.assert_called_with('Task starting: %s[%s]', task.name, task_id)
    mock_connection.close.assert_called_once()

def test_task_postrun_handler(mock_logger, mock_connection):
    """Test post-task execution handling."""
    task = Mock()
    task.name = 'test_task'
    task_id = 'test-id-123'
    state = 'SUCCESS'
    
    task_postrun_handler(task_id=task_id, task=task, args=(), kwargs={}, retval=None, state=state)
    
    # Verify logging
    mock_logger.info.assert_called_with('Task complete: %s[%s] -> %s', task.name, task_id, state)
    mock_connection.close.assert_called_once()

def test_task_sent_handler(mock_logger):
    """Test task queuing notification."""
    sender = 'test_task'
    headers = {'id': 'test-id-123', 'task': 'test_task'}
    body = None
    
    task_sent_handler(sender=sender, headers=headers, body=body)
    
    # Verify logging
    mock_logger.info.assert_called_with('Task sent to queue: %s', sender)

def test_celery_logging_configuration():
    """Test Celery logging configuration."""
    setup_celery_logging()

def test_task_success_handler(mock_logger):
    """Test successful task completion handling."""
    sender = Mock()
    sender.name = 'test_task'
    task_id = 'test-id-123'
    result = 'success'
    
    task_success_handler(sender=sender, task_id=task_id, result=result)
    
    # Verify success logging
    mock_logger.info.assert_called_with('Task succeeded: %s[%s] -> %s', sender.name, task_id, result)

def test_task_failure_handler(mock_logger):
    """Test failed task handling."""
    sender = Mock()
    sender.name = 'test_task'
    task_id = 'test-id-123'
    exception = ValueError('Test error')
    einfo = Mock()
    
    task_failure_handler(sender=sender, task_id=task_id, exception=exception, einfo=einfo)
    
    # Verify error logging
    mock_logger.error.assert_called_with(
        'Task failed: %s[%s] - %s: %s',
        sender.name,
        task_id,
        type(exception).__name__,
        str(exception)
    )

def test_task_retry_policy():
    """Test task retry policy configuration."""
    # Verify default retry settings
    assert app.conf.task_acks_late is True
    assert app.conf.task_reject_on_worker_lost is True
