import pytest
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from core.models.user import kUser
from core.models.contact import Contact
from core.models.message import Message
from core.models.messagelog import MessageLogs
from core.models.userphone import UserPhone

class TestSentMessagesAuth(APITestCase):
    """Simplified tests for Sent Messages API authentication"""
    
    @classmethod
    def setUpTestData(cls):
        # Clear all existing data first
        MessageLogs.objects.all().delete()
        Message.objects.all().delete()
        Contact.objects.all().delete()
        UserPhone.objects.all().delete()
        kUser.objects.all().delete()
        
        # Create test user
        cls.user = kUser.objects.create(
            name='Test User',
            email='test@example.com',
            company='Test Company',
            password='testpass123'
        )
        cls.user.set_password('testpass123')
        cls.user.save()
        
        # Create a valid token
        cls.token = str(AccessToken.for_user(cls.user))
        
        # Create minimal required data
        cls.user_phone = UserPhone.objects.create(
            user=cls.user,
            phone_number='+1234567890',
            phone_token='testtoken',
            phone_description='Test Phone'
        )
        
        cls.contact = Contact.objects.create(
            name='Test Contact',
            phone='+1987654321',
            user=cls.user,
            relationship_tag='test-tag'
        )
        
        cls.message = Message.objects.create(
            title='Test Message',
            text='Hello, World!',
            user=cls.user,
            relationship_tag='test-tag'
        )
        
        # Create one test message log
        cls.message_log = MessageLogs.objects.create(
            message=cls.message,
            user=cls.user,
            user_phone=cls.user_phone,
            contact=cls.contact,
            status='sent',
            relationship_tag='test-tag'
        )
        
        # API endpoint
        cls.sent_messages_url = '/api/messagelogs/'
    
    def setUp(self):
        self.client = APIClient()
        # Start with no authentication
        self.client.credentials()
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users get 401 Unauthorized"""
        # Clear any authentication
        self.client.credentials()
        response = self.client.get(self.sent_messages_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_invalid_token_denied(self):
        """Test that invalid tokens are rejected"""
        # Set invalid token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid.token.here')
        response = self.client.get(self.sent_messages_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    # TODO
    # def test_authenticated_access_allowed(self):
    #     """Test that authenticated users can access the endpoint"""
    #     print(f"\nToken being used: {self.token}")
    #     self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    #     response = self.client.get(self.sent_messages_url)
    #     print(f"Response status: {response.status_code}")
    #     print(f"Response data: {response.data}")
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(response.data['count'], 1)