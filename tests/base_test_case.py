from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()

class BaseAPITestCase(APITestCase):    
    def setUp(self):
        """Set up test data and authentication"""
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True
        )
        
        # Generate JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
        # Set up the client with the token
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
