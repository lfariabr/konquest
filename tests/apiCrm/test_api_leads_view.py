from django.test import Client
import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_leads_view():
    client = Client()
    response = client.get(reverse('leads'))  # Updated URL name
    assert response.status_code == 200