from django_daisy.admin import DaisyAdminSite
from django.contrib.admin.models import LogEntry
from django.contrib import admin

class KonquestAdmin(DaisyAdminSite):
    # Override the logo with our custom one
    logo = '/static/img/logo.svg'
    site_title = 'konquista'
    site_header = 'konquista Admin'

# Replace the default admin site
admin_site = KonquestAdmin()
# Register the LogEntry model
admin_site.register(LogEntry)

for model, model_admin in admin.site._registry.items():
    if model is not LogEntry:
        admin_site.register(model, type(model_admin))



# from django.contrib.admin.views.main import ChangeList
# from django.http import HttpResponse

# class DashboardView(ChangeList):
#     def get_queryset(self, request):
#         return Contact.objects.all().count()

#     def changelist_view(self, request, extra_context=None):
#         # Display key metrics (e.g., active users, leads, etc.)
#         total_contacts = Contact.objects.count()
#         total_leads = Contact.objects.filter(is_lead=True).count()

#         extra_context = extra_context or {}
#         extra_context['total_contacts'] = total_contacts
#         extra_context['total_leads'] = total_leads

#         return super().changelist_view(request, extra_context=extra_context)

# admin_site.register_view('dashboard/', view=DashboardView.as_view())