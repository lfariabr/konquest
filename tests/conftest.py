import urllib3
import warnings
import pytest
from django.test import TransactionTestCase
from django.db import connections

# Disable InsecureRequestWarning globally for all tests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]

@pytest.fixture(autouse=True)
def clean_database():
    """Clean up database after each test."""
    yield
    # Clean up after each test
    for db_name in connections:
        connection = connections[db_name]
        connection.close()
