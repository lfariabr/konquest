from django.test import TestCase
from django.core.management import call_command
from unittest.mock import patch, MagicMock
from io import StringIO

class TestRunScheduler(TestCase):
    @patch('messageShooter.management.commands.run_scheduler.CampaignScheduler')
    @patch('messageShooter.management.commands.run_scheduler.QueueProcessor')
    def test_command_processes_campaigns_and_queue(self, mock_queue_processor, mock_scheduler):
        """Test that command processes both campaigns and queue"""
        # Setup mocks
        mock_scheduler_instance = MagicMock()
        mock_scheduler_instance.process_campaigns.return_value = 1
        mock_scheduler.return_value = mock_scheduler_instance
        
        # Call command
        out = StringIO()
        call_command('run_scheduler', test_mode=True, stdout=out)
        
        # Check output
        output = out.getvalue()
        self.assertIn("Created 1 new queue items for campaigns", output)
        self.assertIn("Stopping campaign scheduler service", output)

    def test_command_handles_keyboard_interrupt(self):
        """Test that command handles keyboard interrupt gracefully"""
        # Call command
        out = StringIO()
        with patch('messageShooter.services.scheduler.CampaignScheduler.process_campaigns') as mock_process:
            mock_process.side_effect = KeyboardInterrupt()
            call_command('run_scheduler', test_mode=True, stdout=out)
        
        # Check output
        output = out.getvalue()
        self.assertIn("Starting campaign scheduler service", output)
        self.assertIn("Stopping campaign scheduler service", output)

    @patch('messageShooter.management.commands.run_scheduler.CampaignScheduler')
    def test_command_handles_processing_errors(self, mock_scheduler):
        """Test that command handles processing errors gracefully"""
        # Setup mock to raise error
        mock_scheduler_instance = MagicMock()
        mock_scheduler_instance.process_campaigns.side_effect = Exception("Campaign processing error")
        mock_scheduler.return_value = mock_scheduler_instance
        
        # Call command
        out = StringIO()
        call_command('run_scheduler', test_mode=True, stdout=out)
        
        # Check output
        output = out.getvalue()
        self.assertIn("Error processing campaigns: Campaign processing error", output)
        self.assertIn("Stopping campaign scheduler service", output)
