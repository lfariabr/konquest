from django_daisy.admin import DaisyAdminSite
from django.contrib.admin.models import LogEntry
from django.contrib import admin

class KonquestAdmin(DaisyAdminSite):
    # Override the logo with our custom one
    logo = '/static/img/logo.svg'
    # You can also customize other attributes here if needed
    site_title = 'konquista'
    site_header = 'konquista Admin'

# Replace the default admin site
admin_site = KonquestAdmin()

# Register the LogEntry model
admin_site.register(LogEntry)

# Re-register all the models that were registered with the default admin site
for model, model_admin in admin.site._registry.items():
    if model is not LogEntry:  # Skip LogEntry as we've already registered it
        admin_site.register(model, type(model_admin))
