import pytest
from django.test import Client
from django.urls import reverse

@pytest.mark.django_db
def test_appointments_view():
    client = Client()
    response = client.get(reverse('appointments_view'))  # assuming 'appointments_view' is the route name
    assert response.status_code == 200