import urllib3
import warnings

# Disable InsecureRequestWarning globally for all tests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]
