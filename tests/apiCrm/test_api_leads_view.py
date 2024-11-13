import pytest
from django.test import Client
from django.urls import reverse

@pytest.mark.django_db
def test_leads_view():
    client = Client()
    response = client.get(reverse('leads_view'))  # assuming 'leads_view' is the name in your urls.py for this route
    assert response.status_code == 200