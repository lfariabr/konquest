# apiCrm/schemas/resolve_all_data
import logging
import aiohttp
import graphene
import pandas as pd
from decouple import config
from asgiref.sync import async_to_sync
from apiCrm.schemas.lead_type import LeadType
from apiCrm.schemas.all_data_type import AllDataType
from apiCrm.schemas.appointment_type import AppointmentType
from apiCrm.schemas.bill_charges_type import BillChargeType
from apiCrm.resolvers.fetch_all_data import run_fetch_all
from apiCrm.resolvers.fetch_all_leads import fetch_all_leads
from apiCrm.resolvers.fetch_bill_charges import fetch_bill_charges
from apiCrm.resolvers.fetch_all_appointments import fetch_all_appointments
from apiCrm.utils.format_lead_data import format_lead_data
from apiCrm.utils.format_appointment_data import format_appointment_data
from apiCrm.utils.format_bill_charge_data import format_bill_charge_data
from apiCrm.serializers import LeadSerializer, AppointmentSerializer, BillChargeSerializer
from datetime import datetime, timedelta, timezone
from graphene_django.types import DjangoObjectType
from django.db import transaction


logger = logging.getLogger(__name__)
token = config('TOKEN')

class Query(graphene.ObjectType):
    leads = graphene.List(LeadType, start_date=graphene.String(), end_date=graphene.String())
    appointments = graphene.List(AppointmentType, start_date=graphene.String(), end_date=graphene.String())
    bill_charges = graphene.List(BillChargeType, start_date=graphene.String(), end_date=graphene.String())

    all_data = graphene.Field(
        AllDataType,
        start_date=graphene.String(required=True),
        end_date=graphene.String(required=True),
        extended_end_date=graphene.String(required=True),
    )

    def resolve_all_data(self, info, start_date, end_date, extended_end_date):
        print(f"Starting processing for start_date: {start_date}, end_date: {end_date}, extended_end_date: {extended_end_date}")
        leads_data, appointments_data, bill_charges_data = fetch_data(start_date, end_date, extended_end_date, token)
        leads_instances = process_leads(leads_data)
        appointments_instances = process_appointments(appointments_data)
        bill_charges_instances = process_bill_charges(bill_charges_data)
        all_data = assemble_all_data(leads_instances, appointments_instances, bill_charges_instances)
        print("___")
        print("ALL DATA HAS BEEN RESOLVED!")
        return all_data

    def resolve_leads(self, info, start_date, end_date):
        def sync_fetch_leads(start_date, end_date, token):
            async def async_fetch():
                async with aiohttp.ClientSession() as session:
                    return await fetch_all_leads(session, start_date, end_date, token)
            return async_to_sync(async_fetch)()

        leads_data = sync_fetch_leads(start_date, end_date, token)
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

        for lead_data in leads_results_list:
            serializer = LeadSerializer(data=lead_data)
            if serializer.is_valid():
                serializer.save()
            else:
                print(f"Failed to save lead: {serializer.errors}")

        return [LeadType(**lead_data) for lead_data in leads_results_list]
    
    def resolve_appointments(self, info, start_date, end_date):
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        extended_end_date_obj = end_date_obj + timedelta(days=15)

        start_date_str = start_date_obj.strftime('%Y-%m-%d')
        end_date_str = end_date_obj.strftime('%Y-%m-%d')
        extended_end_date_str = extended_end_date_obj.strftime('%Y-%m-%d')

        def sync_fetch_appointments(start_date, end_date, token):
            async def async_fetch():
                async with aiohttp.ClientSession() as session:
                    return await fetch_all_appointments(session, start_date, end_date, token)
            return async_to_sync(async_fetch)()

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
        def sync_fetch_bill_charges(start_date, end_date, token):
            async def async_fetch():
                async with aiohttp.ClientSession() as session:
                    return await fetch_bill_charges(session, start_date, end_date, token)
            return async_to_sync(async_fetch)()

        bill_charges_data = sync_fetch_bill_charges(start_date, end_date, token)

        bill_charges_results_list = []
        for data_row in bill_charges_data:
            quote = data_row["quote"]
            customer_email = quote["customer"].get("email", "")
            if not customer_email:
                customer_email = "N/A"
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
            
            serializer = BillChargeSerializer(data=formatted_row)
            if serializer.is_valid():
                serializer.save()
            else:
                print(f"Failed to save bill charge: {serializer.errors}")

            bill_charges_results_list.append(formatted_row)

        return [BillChargeType(**bill_charge) for bill_charge in bill_charges_results_list]

schema = graphene.Schema(query=Query)

def fetch_data(start_date, end_date, extended_end_date, token):
        try:
            leads_data, appointments_data, bill_charges_data = run_fetch_all(start_date, end_date, extended_end_date, token)
            return leads_data, appointments_data, bill_charges_data
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return None, None, None
        
# def process_leads(leads_data):
#     try:
#         leads_instances = []
#         for raw_lead in leads_data:
#             serializer = LeadSerializer(data=format_lead_data(raw_lead))
#             if serializer.is_valid():
#                 lead_instance = serializer.save()
#                 leads_instances.append(lead_instance)
#             else:
#                 logger.error(f"Error saving lead: {serializer.errors}")
#         return leads_instances
#     except Exception as e:
#         logger.error(f"Error processing leads: {e}")
#         print(f"Error processing leads: {e}")
#         return []

def process_leads(leads_data):
    try:
        leads_instances = []
        with transaction.atomic():
            for raw_lead in leads_data:
                formatted_data = format_lead_data(raw_lead)
                print(f"Processing lead {formatted_data.get('id_crm', 'unknown')}")
                serializer = LeadSerializer(data=formatted_data)
                if serializer.is_valid():
                    lead_instance = serializer.save()
                    leads_instances.append(lead_instance)
                else:
                    print(f"Error saving lead: {serializer.errors}")
                    logger.error(f"Error saving lead: {serializer.errors}")
            print(f"Successfully processed {len(leads_instances)} leads")
        return leads_instances
    except Exception as e:
        print(f"Error processing leads: {str(e)}")
        logger.error(f"Error processing leads: {e}")
        return []

# def process_appointments(appointments_data):
#     try:
#         appointments_instances = []
#         for raw_appointment in appointments_data:
#             serializer = AppointmentSerializer(data=format_appointment_data(raw_appointment))
#             if serializer.is_valid():
#                 appointment_instance = serializer.save()
#                 appointments_instances.append(appointment_instance)
#             else:
#                 logger.error(f"Error saving appointment: {serializer.errors}")
#         return appointments_instances
#     except Exception as e:
#         logger.error(f"Error processing appointments: {e}")
#         print(f"Error processing appointments: {e}")
#         return []
def process_appointments(appointments_data):
    try:
        appointments_instances = []
        with transaction.atomic():
            for raw_appointment in appointments_data:
                formatted_data = format_appointment_data(raw_appointment)
                print(f"Processing appointment {formatted_data.get('id_crm', 'unknown')}")
                serializer = AppointmentSerializer(data=formatted_data)
                if serializer.is_valid():
                    appointment_instance = serializer.save()
                    appointments_instances.append(appointment_instance)
                else:
                    print(f"Error saving appointment: {serializer.errors}")
                    logger.error(f"Error saving appointment: {serializer.errors}")
            print(f"Successfully processed {len(appointments_instances)} appointments")
        return appointments_instances
    except Exception as e:
        print(f"Error processing appointments: {str(e)}")
        logger.error(f"Error processing appointments: {e}")
        return []
    
# def process_bill_charges(bill_charges_data):
#     try:
#         bill_charges_instances = []
#         for raw_bill_charge in bill_charges_data:
#             serializer = BillChargeSerializer(data=format_bill_charge_data(raw_bill_charge))
#             if serializer.is_valid():
#                 bill_charge_instance = serializer.save()
#                 bill_charges_instances.append(bill_charge_instance)
#             else:
#                 logger.error(f"Error saving bill charge: {serializer.errors}")
#         return bill_charges_instances
#     except Exception as e:
#         logger.error(f"Error processing bill charges: {e}")
#         print(f"Error processing bill charges: {e}")
#         return []
def process_bill_charges(bill_charges_data):
    try:
        bill_charges_instances = []
        with transaction.atomic():
            for raw_bill_charge in bill_charges_data:
                formatted_data = format_bill_charge_data(raw_bill_charge)
                print(f"Processing bill charge {formatted_data.get('quote_id', 'unknown')}")
                serializer = BillChargeSerializer(data=formatted_data)
                if serializer.is_valid():
                    bill_charge_instance = serializer.save()
                    bill_charges_instances.append(bill_charge_instance)
                else:
                    print(f"Error saving bill charge: {serializer.errors}")
                    logger.error(f"Error saving bill charge: {serializer.errors}")
            print(f"Successfully processed {len(bill_charges_instances)} bill charges")
        return bill_charges_instances
    except Exception as e:
        print(f"Error processing bill charges: {str(e)}")
        logger.error(f"Error processing bill charges: {e}")
        return []

def assemble_all_data(leads_instances, appointments_instances, bill_charges_instances):
    try:
        return AllDataType(leads=leads_instances, appointments=appointments_instances, bill_charges=bill_charges_instances)
    except Exception as e:
        logger.error(f"Error assembling all data: {e}")
        return None