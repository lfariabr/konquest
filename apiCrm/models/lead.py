from django.db import models
from apiCrm.dicts.dict_store_ident import dic_store_ident
from apiCrm.dicts.dict_region_ident import dic_region_ident
from apiCrm.utils.create_store import create_store
from apiCrm.utils.create_region import create_region
from decouple import config
import requests

GRAPHQL_URL = 'https://open-api.eprocorpo.com.br/graphql'

class Lead(models.Model):
    # CRM fields
    id_crm = models.CharField(max_length=100)
    name = models.CharField(max_length=150)
    email = models.CharField(max_length=100)
    phone = models.CharField(max_length=100, db_index=True)
    source = models.CharField(max_length=100)
    store = models.CharField(max_length=100, null=True, blank=True)
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

    class Meta:
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['id_crm']),
            models.Index(fields=['store']),
        ]

    def create_leads_at_crm(self, name, phone, email, message, store, region):
        source_identifier = "662bf789-d04c-4ccf-8424-26b92595060c"
        store_identifier = dic_store_ident[store]
        region_identifier = dic_region_ident[region]
        
        # Format phone number - remove any non-digit characters
        phone = ''.join(filter(str.isdigit, str(phone)))

        query = """
            mutation ($data: CreateLeadInput!) {
                createLead(
                    data: $data
                ) {
                    email
                    name
                    message
                    region {
                        identifier
                    }
                    source {
                        identifier
                    }
                    store {
                        identifier
                    }
                    telephone
                }
            }
        """
        variables = {
            "data": {
                "email": email,
                "message": message,
                "name": name,
                "regionIdentifier": region_identifier,
                "sourceIdentifier": source_identifier,
                "storeIdentifier": store_identifier,
                "telephone": phone
            }
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {config("TOKEN")}'
        }
        response = requests.post(GRAPHQL_URL, json={'query': query, 'variables': variables}, headers=headers)
        response_data = response.json()

        if response.status_code == 200:
            print("Lead created successfully:", response_data)
        else:
            print("Failed to create lead:", response_data)

        return response_data