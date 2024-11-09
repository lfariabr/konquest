from django.db import models

class Lead(models.Model):
    id = models.AutoField(primary_key=True)

    # CRM fields
    id_crm = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    phone = models.CharField(max_length=100)
    source = models.CharField(max_length=100)
    store = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    customer_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField()

    # Extra cool fields to have
    utm_medium = models.CharField(max_length=100, null=True, blank=True)
    utm_campaign = models.CharField(max_length=100, null=True, blank=True)
    utm_content = models.CharField(max_length=100, null=True, blank=True)
    utm_search = models.CharField(max_length=100, null=True, blank=True)
    utm_term = models.CharField(max_length=100, null=True, blank=True)
    message = models.TextField(null=True, blank=True)

class Appointment(models.Model):
    id = models.AutoField(primary_key=True)

    # CRM fields
    id_crm = models.CharField(max_length=100)
    status_label = models.CharField(max_length=100)
    store_name = models.CharField(max_length=100)
    customer_id = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=100)
    procedure_name = models.CharField(max_length=100)
    procedure_group = models.CharField(max_length=100)
    employee_name = models.CharField(max_length=100)
    createdby_name = models.CharField(max_length=100)
    createdby_created_at = models.DateTimeField()
    appointment_date = models.DateTimeField()