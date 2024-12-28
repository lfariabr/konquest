"""
Test Target List Resolver
"""
import pytest
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from messageShooter.resolvers.target_list_resolver import create_target_list, clean_target_list, reprioritize_by_tag
from messageShooter.models.campaign import Campaign, FREQUENCY_ONCE
from messageShooter.models.target_list import TargetList
from core.models.contact import Contact
from core.models.message import Message
from core.models.userphone import UserPhone
from core.models.user import kUser

@pytest.mark.django_db
class TestTargetListResolver(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create test user
        cls.test_user = kUser.objects.create(
            name='Test User',
            email='test@example.com',
            password='test123',
            company='Test Company'
        )
        
        # Create test userphone
        cls.test_userphone = UserPhone.objects.create(
            phone_number='11988888888',
            phone_token='dummy_token',
            relationship_tag='Botox',
            user=cls.test_user
        )
        
        # Create test message
        cls.test_message = Message.objects.create(
            text='Test message',
            relationship_tag='Botox',
            user=cls.test_user,
            title='Test Title'
        )
        
        # Create test campaign
        cls.test_campaign = Campaign.objects.create(
            name='Test Campaign',
            user=cls.test_user,
            userphone=cls.test_userphone,
            contact_type='Whatsapp',
            contact_tag='Botox',  # Match case with message and userphone
            campaign_status='Active',
            frequency=FREQUENCY_ONCE,
            # schedule_type='daily',  # Add schedule type
            # schedule_time='12:00',  # Add schedule time
            # schedule_days=['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']  # Add all days
        )

    @patch('messageShooter.resolvers.target_list_resolver.get_contact_whatsapp')
    @patch('messageShooter.resolvers.target_list_resolver.bulk_get_counter_whatsapp')
    @patch('messageShooter.resolvers.target_list_resolver.get_message')
    def test_create_target_list_success(self, mock_get_message, mock_get_counter, mock_get_contacts):
        """Test successful target list creation"""
        # Setup mock returns
        test_contact = Contact.objects.create(
            phone='11999999999',
            name='Test Contact',
            user=self.test_user
        )
        mock_get_contacts.return_value = [test_contact]
        mock_get_counter.return_value = {'11999999999': 0}
        mock_get_message.return_value = self.test_message
        
        # Execute with force_run=True to bypass schedule checks
        created, skipped, errors = create_target_list(self.test_campaign.id, force_run=True)
        
        # Assert
        assert created == 1
        assert skipped == 0
        assert errors == 0
        assert TargetList.objects.count() == 1
        
        target_list = TargetList.objects.first()
        assert target_list.campaign == self.test_campaign
        assert target_list.contact == test_contact
        assert target_list.message == self.test_message
        assert target_list.status == 'pending'

    def test_clean_target_list(self):
        """Test cleaning old target list entries"""
        # Create old target list
        old_date = timezone.now() - timezone.timedelta(days=8)
        target_list = TargetList.objects.create(
            campaign=self.test_campaign,
            contact=Contact.objects.create(
                phone='11999999999',
                name='Test Contact',
                user=self.test_user
            ),
            message=self.test_message,
            contact_tag='botox',
            contact_type='Whatsapp',
            contact_phone='11999999999',
            userphone=self.test_userphone,
            token='dummy_token',
            status='pending'
        )
        TargetList.objects.filter(id=target_list.id).update(created_at=old_date)
        
        # Execute
        deleted_count = clean_target_list()
        
        # Assert
        assert deleted_count == 1
        assert TargetList.objects.count() == 0

    def test_reprioritize_by_tag(self):
        """Test reprioritizing target lists by tag"""
        # Create test target list
        target_list = TargetList.objects.create(
            campaign=self.test_campaign,
            contact=Contact.objects.create(
                phone='11999999999',
                name='Test Contact',
                user=self.test_user
            ),
            message=self.test_message,
            contact_tag='botox',
            contact_type='Whatsapp',
            contact_phone='11999999999',
            userphone=self.test_userphone,
            token='dummy_token',
            status='pending'
        )
        
        # Execute
        updated_count = reprioritize_by_tag('botox', 5)
        
        # Assert
        assert updated_count == 1
        target_list.refresh_from_db()
        assert target_list.priority == 5
