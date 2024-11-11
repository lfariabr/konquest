# apiCrm/schema.py
import asyncio
import graphene
import pandas as pd
from graphene_django.types import DjangoObjectType
from .models import Lead, Appointment
from .resolvers import (
    fetch_all_leads,
    fetch_all_appointments,
    fetch_bill_charges,
    fetch_all_data,
    run_fetch_all
)
from .serializers import LeadSerializer, AppointmentSerializer, BillChargeSerializer
from datetime import datetime, timedelta, timezone, date, time
from decouple import config
import aiohttp
from asgiref.sync import async_to_sync
from .utils import format_lead_data, format_appointment_data, format_bill_charge_data

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
        
        def resolve_id(self, info):
            return self.id_crm  # Ensure that `id` maps to `id_crm`
        
class BillChargeType(graphene.ObjectType):
    id = graphene.String()  # Define `id` field for GraphQL
    quote_id = graphene.String()
    customer_id = graphene.String()
    customer_name = graphene.String()
    customer_taxvat = graphene.String()
    customer_email = graphene.String()
    store_name = graphene.String()
    total_amount = graphene.Float()
    installments = graphene.Int()
    paid_at = graphene.String()
    due_at = graphene.String()
    is_paid = graphene.Boolean()
    payment_method = graphene.String()
    status = graphene.String()
    quote_items = graphene.String()

    def resolve_id(self, info):
        return self.quote_id  # Return `quote_id` as `id` in the GraphQL response

class AllDataType(graphene.ObjectType):
    leads = graphene.List(LeadType)
    appointments = graphene.List(AppointmentType)
    bill_charges = graphene.List(BillChargeType)

class Query(graphene.ObjectType):
    leads = graphene.List(LeadType, start_date=graphene.String(), end_date=graphene.String())
    appointments = graphene.List(AppointmentType, start_date=graphene.String(), end_date=graphene.String())
    bill_charges = graphene.List(BillChargeType, start_date=graphene.String(), end_date=graphene.String())

    all_data = graphene.Field(
        AllDataType,
        start_date=graphene.String(required=True),
        end_date=graphene.String(required=True),
        extended_end_date=graphene.String(required=True),
        # No need to explicitly assign the resolver if it follows the naming convention
    )
    
    def resolve_all_data(self, info, start_date, end_date, extended_end_date):
        print(f"Starting period from {start_date} to {end_date} with extended end date {extended_end_date}")

        token = config('TOKEN')
        leads_data, appointments_data, bill_charges_data = run_fetch_all(start_date, end_date, extended_end_date, token)

        # Lists to hold model instances
        leads_instances = []
        appointments_instances = []
        bill_charges_instances = []

        for raw_lead in leads_data:
            serializer = LeadSerializer(data=format_lead_data(raw_lead))
            if serializer.is_valid():
                lead_instance = serializer.save()
                leads_instances.append(lead_instance)
            else:
                print(f"Failed to save lead: {serializer.errors}")

        for raw_appointment in appointments_data:
            serializer = AppointmentSerializer(data=format_appointment_data(raw_appointment))
            if serializer.is_valid():
                appointment_instance = serializer.save()
                appointments_instances.append(appointment_instance)
            else:
                print(f"Failed to save appointment: {serializer.errors}")

        for raw_bill_charge in bill_charges_data:
            serializer = BillChargeSerializer(data=format_bill_charge_data(raw_bill_charge))
            if serializer.is_valid():
                bill_charge_instance = serializer.save()
                bill_charges_instances.append(bill_charge_instance)
            else:
                print(f"Failed to save bill charge: {serializer.errors}")

        print("All data resolved successfully. Returning results to client.")

        # Return GraphQL types, directly utilizing the instances
        return AllDataType(
            leads=leads_instances,
            appointments=appointments_instances,
            bill_charges=bill_charges_instances
        )   
    
    def resolve_leads(self, info, start_date, end_date):
        token = config('TOKEN')
    
        # Define a synchronous wrapper function for `fetch_all_leads`
        def sync_fetch_leads(start_date, end_date, token):
            async def async_fetch():
                async with aiohttp.ClientSession() as session:
                    return await fetch_all_leads(session, start_date, end_date, token)
            return async_to_sync(async_fetch)()

        # Call the synchronous wrapper
        leads_data = sync_fetch_leads(start_date, end_date, token)
        
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

        # Define a synchronous wrapper function for `fetch_all_appointments`
        def sync_fetch_appointments(start_date, end_date, token):
            async def async_fetch():
                async with aiohttp.ClientSession() as session:
                    return await fetch_all_appointments(session, start_date, end_date, token)
            return async_to_sync(async_fetch)()

        # Call the synchronous wrapper
        appointments_data = sync_fetch_appointments(start_date_str, extended_end_date_str, token)

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
    
    def resolve_bill_charges(self, info, start_date, end_date):
        token = config("TOKEN")  # Ensure token is retrieved

        # Define a synchronous wrapper function for `fetch_bill_charges`
        def sync_fetch_bill_charges(start_date, end_date, token):
            async def async_fetch():
                async with aiohttp.ClientSession() as session:
                    return await fetch_bill_charges(session, start_date, end_date, token)
            return async_to_sync(async_fetch)()

        # Call the synchronous wrapper
        bill_charges_data = sync_fetch_bill_charges(start_date, end_date, token)

        bill_charges_results_list = []
        for data_row in bill_charges_data:
            quote = data_row["quote"]
            formatted_row = {
                'quote_id': quote["id"],
                'customer_id': quote["customer"]["id"],
                'customer_name': quote["customer"]["name"],
                'customer_taxvat': quote["customer"].get("taxvat", "N/A"),
                'customer_email': quote["customer"].get("email", ""),
                'store_name': data_row["store"]["name"],
                'total_amount': quote["bill"]["total"],
                'installments': quote["bill"].get("installmentsQuantity", "N/A"),
                'paid_at': data_row.get("paidAt", "N/A"),
                'due_at': data_row.get("dueAt", "N/A"),
                'is_paid': data_row["isPaid"],
                'payment_method': data_row["paymentMethod"]["name"],
                'status': quote["status"],
                'quote_items': "; ".join([f"{item['description']} (Qty: {item['quantity']}, Amount: {item['amount']})" for item in quote["bill"]["items"]])
            }
            
            # Save the data to the database using the serializer
            serializer = BillChargeSerializer(data=formatted_row)
            if serializer.is_valid():
                serializer.save()
            else:
                print(f"Failed to save bill charge: {serializer.errors}")

            bill_charges_results_list.append(formatted_row)

        # Return the results as GraphQL BillChargeType instances
        return [BillChargeType(**bill_charge) for bill_charge in bill_charges_results_list]
    
schema = graphene.Schema(query=Query)