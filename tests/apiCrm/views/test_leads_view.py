from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apiCrm.models.lead import Lead
from apiCrm.serializers import LeadSerializer
from django.utils import timezone

class LeadsViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.leads_url = reverse('leads')
        
        # Create test leads
        self.lead1 = Lead.objects.create(
            id_crm="123",
            name="Test Lead 1",
            phone="11987654321",
            store="Test Store 1",
            status="Active",
            created_at=timezone.now()
        )
        self.lead2 = Lead.objects.create(
            id_crm="456",
            name="Test Lead 2",
            phone="11987654322",
            store="Test Store 2",
            status="Inactive",
            created_at=timezone.now()
        )

    def test_get_all_leads(self):
        """Test retrieving all leads"""
        response = self.client.get(self.leads_url)
        leads = Lead.objects.all()
        serializer = LeadSerializer(leads, many=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(len(response.data), 2)

    def test_get_leads_check_content(self):
        """Test the content of retrieved leads"""
        response = self.client.get(self.leads_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['id_crm'], "123")
        self.assertEqual(response.data[0]['name'], "Test Lead 1")
        self.assertEqual(response.data[0]['phone'], "11987654321")
        self.assertEqual(response.data[0]['store'], "Test Store 1")
        self.assertEqual(response.data[0]['status'], "Active")

    def test_get_leads_no_leads(self):
        """Test retrieving leads when none exist"""
        Lead.objects.all().delete()
        response = self.client.get(self.leads_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_leads_url_exists(self):
        """Test that the leads URL exists and resolves"""
        response = self.client.get(self.leads_url)
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_leads_only_allows_get(self):
        """Test that only GET method is allowed"""
        response_post = self.client.post(self.leads_url, {})
        response_put = self.client.put(self.leads_url, {})
        response_delete = self.client.delete(self.leads_url)
        
        self.assertEqual(response_post.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response_put.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response_delete.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
