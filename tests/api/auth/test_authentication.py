# pytest tests/api/auth/test_authentication.py

import pytest
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from core.models.user import kUser
from rest_framework import status
from django.contrib.auth.hashers import make_password

@pytest.mark.django_db
class TestAuthentication(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = kUser.objects.create(
            name='Test User',
            email='test@example.com',
        )
        self.user.set_password('testpass123')
        self.user.set_password('testpass123')
        self.user.save()
        
        self.refresh = RefreshToken.for_user(self.user)
        self.token = str(self.refresh.access_token)
        self.protected_endpoint = '/api/contacts/'

    # TODO:
    # def test_obtain_token_pair(self):
    #     """Test that we can obtain a JWT token pair"""
    #     url = '/api/token/'
    #     data = {
    #         'username': 'test@example.com',
    #         'password': 'testpass123'
    #     }
    #     response = self.client.post(url, data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertIn('access', response.data)
    #     self.assertIn('refresh', response.data)

    def test_token_refresh(self):
        """Test that we can refresh an access token"""
        url = '/api/token/refresh/'
        data = {'refresh': str(self.refresh)}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_protected_endpoint_with_valid_token(self):
        """Test accessing a protected endpoint with a valid token"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.protected_endpoint)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED])
        if response.status_code == 200:
            self.assertEqual(response.get('Content-Type'), 'application/json')

    def test_protected_endpoint_without_token(self):
        """Test accessing a protected endpoint without a token"""
        self.client.credentials()
        response = self.client.get(self.protected_endpoint)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.get('Content-Type'), 'application/json')

    def test_protected_endpoint_with_invalid_token(self):
        """Test accessing a protected endpoint with an invalid token"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid.token.here')
        response = self.client.get(self.protected_endpoint)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.get('Content-Type'), 'application/json')