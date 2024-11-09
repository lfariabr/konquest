# apiCrm/schema.py
import graphene
from graphene_django.types import DjangoObjectType
from .models import Lead, Appointment
from .resolvers import fetch_all_leads, fetch_all_appointments
import asyncio
import pandas as pd
from .serializers import LeadSerializer, AppointmentSerializer
from datetime import datetime, timedelta, timezone, date, time
from decouple import config

class LeadType(DjangoObjectType):
    class Meta:
        model = Lead
        fields = '__all__'

class AppointmentType(DjangoObjectType):
        appointment_date = graphene.DateTime()
        createdby_created_at = graphene.DateTime()
        
        class Meta:
            model = Appointment
            fields = '__all__'
        
        

class Query(graphene.ObjectType):
    leads = graphene.List(LeadType, start_date=graphene.String(), end_date=graphene.String())
    appointments = graphene.List(AppointmentType, start_date=graphene.String(), end_date=graphene.String())

    def resolve_leads(self, info, start_date, end_date):
        token = config("TOKEN")
    
        # Executa a busca de leads usando a função fetch_all_leads de maneira assíncrona
        leads_data = asyncio.run(fetch_all_leads(start_date, end_date, token))
        
        # Ensure leads_results_list contains dictionaries, not LeadType instances
        leads_results_list = []
        
        for lead in leads_data:
            formatted_row = {
                'id_crm': lead['id'],
                'name': lead['name'],
                'email': lead['email'],
                'phone': lead['telephone'],
                'source': lead['source']['title'],
                'store': lead['store']['name'] if lead['store'] else None,
                'status': lead['status']['label'],
                'customer_id': lead['customer']['id'] if lead['customer'] else None,
                'created_at': lead['createdAt'],
                
                # Optional fields
                'utm_medium': lead.get('utmMedium'),
                'utm_campaign': lead.get('utmCampaign'),
                'utm_content': lead.get('utmContent'),
                'utm_search': lead.get('utmSearch'),
                'utm_term': lead.get('utmTerm'),
                'message': lead.get('message')
            }
            leads_results_list.append(formatted_row)

        # Save each lead to the database
        for lead_data in leads_results_list:
            serializer = LeadSerializer(data=lead_data)
            if serializer.is_valid():
                serializer.save()
            else:
                print(f"Failed to save lead: {serializer.errors}")

        # Optionally, return LeadType instances for the GraphQL response
        return [LeadType(**lead_data) for lead_data in leads_results_list]
    
    def resolve_appointments(self, info, start_date, end_date):
        token = config("TOKEN")
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        extended_end_date_obj = end_date_obj + timedelta(days=15)

        start_date_str = start_date_obj.strftime('%Y-%m-%d')
        end_date_str = end_date_obj.strftime('%Y-%m-%d')
        extended_end_date_str = extended_end_date_obj.strftime('%Y-%m-%d')

        appointments_data = asyncio.run(fetch_all_appointments(start_date_str, end_date_str, token))
        appointments_results_list = []
        for appointment in appointments_data:
            formatted_row = {
                'id_crm': appointment['id'],
                'status_label': appointment.get('status', {}).get('label', 'N/A'),
                'store_name': appointment.get('store', {}).get('name', 'N/A'),
                'customer_id': appointment.get('customer', {}).get('id', 'N/A'),
                'customer_name': appointment.get('customer', {}).get('name', 'N/A'),
                'customer_phone': (
                    appointment.get('customer', {}).get('telephones', [{}])[0].get('number', 'N/A')
                    if isinstance(appointment.get('customer'), dict) and appointment.get('customer', {}).get('telephones')
                    else 'N/A'
                ),
                'procedure_name': appointment.get('procedure', {}).get('name', 'N/A'),
                'procedure_group': appointment.get('procedure', {}).get('groupLabel', 'N/A'),
                'employee_name': appointment.get('employee', {}).get('name', 'N/A'),
                'createdby_name': appointment.get('createdBy', {}).get('name', 'N/A'),
                'createdby_created_at': (
                    datetime.fromisoformat(appointment.get('createdBy', {}).get('createdAt')).astimezone(timezone.utc).isoformat()
                    if appointment.get('createdBy', {}).get('createdAt') else None
                ),
                'appointment_date': (
                    datetime.strptime(appointment.get('startDate'), '%Y-%m-%d %H:%M:%S').astimezone(timezone.utc).isoformat()
                    if appointment.get('startDate') else None
                ),
            }
            appointments_results_list.append(formatted_row)

        for appointment_data in appointments_results_list:
            serializer = AppointmentSerializer(data=appointment_data)
            if serializer.is_valid():
                serializer.save()
            else:
                print(f"Failed to save appointment: {serializer.errors}")

        return [AppointmentType(**appointment_data) for appointment_data in appointments_results_list]
    
    
schema = graphene.Schema(query=Query)