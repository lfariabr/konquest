import pytest
from django.test import Client
from django.urls import reverse

@pytest.mark.django_db
def test_bill_charges_view():
    client = Client()
    response = client.get(reverse('bill_charges_view'))  # assuming 'bill_charges_view' is the route name
    assert response.status_code == 200