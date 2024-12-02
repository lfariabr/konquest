from django.test import TestCase
from django.core.management import call_command
from unittest.mock import patch, MagicMock
from io import StringIO

class TestRunScheduler(TestCase):
    @patch('messageShooter.services.queue_processor.QueueProcessor.process_queue')
    def test_command_processes_queue(self, mock_process):
        """Test that command processes queue"""
        # Setup mock
        mock_process.return_value = (1, 1, 0)
        
        # Call command
        out = StringIO()
        call_command('run_scheduler', stdout=out)
        
        # Check that process_queue was called
        mock_process.assert_called_once()
        
        # Check output
        output = out.getvalue()
        self.assertIn("Processed 1 messages (1 successful, 0 errors)", output)

    def test_command_handles_keyboard_interrupt(self):
        """Test that command handles keyboard interrupt gracefully"""
        # Call command
        out = StringIO()
        with patch('messageShooter.services.queue_processor.QueueProcessor.process_queue') as mock_process:
            mock_process.side_effect = KeyboardInterrupt()
            call_command('run_scheduler', stdout=out)
        
        # Check output
        output = out.getvalue()
        self.assertIn("Error in scheduler: ", output)

    def test_command_handles_processing_errors(self):
        """Test that command handles processing errors gracefully"""
        # Call command
        out = StringIO()
        with patch('messageShooter.services.queue_processor.QueueProcessor.process_queue') as mock_process:
            mock_process.side_effect = Exception("Queue processing error")
            call_command('run_scheduler', stdout=out)
        
        # Check output
        output = out.getvalue()
        self.assertIn("Error in scheduler: Queue processing error", output)

    def test_command_continuous_mode(self):
        """Test that command runs continuously"""
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                raise Exception("Stop test")
            return (1, 1, 0)
            
        with patch('time.sleep') as mock_sleep, \
             patch('messageShooter.services.queue_processor.QueueProcessor.process_queue') as mock_process:
            
            mock_process.side_effect = side_effect
            
            try:
                # Run command in continuous mode
                call_command('run_scheduler', continuous=True, sleep=1)
            except Exception as e:
                if str(e) != "Stop test":
                    raise
            
            # Check that sleep was called
            mock_sleep.assert_called_once_with(1)
            
            # Check that process_queue was called twice
            self.assertEqual(mock_process.call_count, 2)
