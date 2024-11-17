from django.test import Client
import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_appointments_view():
    client = Client()
    response = client.get(reverse('appointments'))  # Updated URL name
    assert response.status_code == 200