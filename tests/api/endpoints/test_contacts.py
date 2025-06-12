# pytest tests/api/endpoints/test_contacts.py -v

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models.user import kUser
from core.models.contact import Contact

class TestContactsAPI(APITestCase):
    """Test cases for the Contacts API endpoint"""
    
    @classmethod
    def setUpTestData(cls):
        # Create test user
        cls.user = kUser.objects.create(
            name='Test User',
            email='test@example.com'
        )
        cls.user.set_password('testpass123')
        cls.user.save()
        
        # Create some test contacts
        Contact.objects.create(
            user=cls.user,
            name='Test Contact 1',
            phone='+1234567890',
            relationship_tag='Test Tag 1'
        )
        Contact.objects.create(
            user=cls.user,
            name='Test Contact 2',
            phone='+1987654321',
            relationship_tag='Test Tag 2'
        )
        
        # Set up URLs
        cls.contacts_url = '/api/contacts/'
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access the contacts endpoint"""
        # Clear any existing credentials
        self.client.credentials()
        
        # Test GET request
        response = self.client.get(self.contacts_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.get('Content-Type'), 'application/json')
        
        # Test POST request
        response = self.client.post(self.contacts_url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test PATCH request
        response = self.client.patch(f"{self.contacts_url}1/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test DELETE request
        response = self.client.delete(f"{self.contacts_url}1/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_authenticated_access_without_token_denied(self):
        """Test that authenticated users without a valid token cannot access the endpoint"""
        # Set an invalid token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid.token.here')
        
        response = self.client.get(self.contacts_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.get('Content-Type'), 'application/json')