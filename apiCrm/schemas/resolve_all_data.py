# apiCrm/schemas/resolve_all_data
import logging
import time
import aiohttp
import graphene
import pandas as pd
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from django.db import transaction, models, utils, connection
from django.core.exceptions import ValidationError
from django.db.utils import OperationalError, IntegrityError
from django.db.models.manager import Manager
from graphene_django.types import DjangoObjectType
from decouple import config
from asgiref.sync import async_to_sync

# Import models
from apiCrm.models.lead import Lead
from apiCrm.models.appointment import Appointment
from apiCrm.models.billcharge import BillCharge  # Note: lowercase billcharge

# Local imports
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
        logger.info(f"Starting data import for period: {start_date} to {end_date} (extended to {extended_end_date})")
        start_time = time.time()
        
        try:
            leads_data, appointments_data, bill_charges_data = fetch_data(start_date, end_date, extended_end_date, token)
            
            # Process all data
            leads_instances = process_leads_batch(leads_data)
            appointments_instances = process_appointments_batch(appointments_data)
            bill_charges_instances = process_bill_charges_batch(bill_charges_data)
            
            all_data = assemble_all_data(leads_instances, appointments_instances, bill_charges_instances)
            
            # Log final statistics
            execution_time = time.time() - start_time
            logger.info(f"Import completed in {execution_time:.2f} seconds")
            
            return all_data
            
        except Exception as e:
            logger.error(f"Error in resolve_all_data: {e}")
            raise

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
        return [], [], []

def process_leads_batch(leads_data: Optional[List[dict]] = None, stats: dict = None, batch_size: int = 1000) -> List[Lead]:
    try:
        if not leads_data:
            logger.warning("No leads data to process")
            return []
            
        leads_instances = []
        total_leads = len(leads_data)
        print(f"\nStarting to process {total_leads} leads in batches of {batch_size}")
        logger.info(f"Starting to process {total_leads} leads in batches of {batch_size}")
        
        for i in range(0, total_leads, batch_size):
            batch = leads_data[i:i + batch_size]
            batch_start = time.time()
            batch_end = min(i+batch_size, total_leads)
            print(f"\nProcessing leads batch {i+1}-{batch_end} of {total_leads}")
            logger.info(f"Processing leads batch {i+1}-{batch_end} of {total_leads}")
            
            def process_batch() -> List[Lead]:
                formatted_batch = [format_lead_data(raw_lead) for raw_lead in batch]
                serializers = [LeadSerializer(data=data) for data in formatted_batch]
                valid_serializers = [s for s in serializers if s.is_valid()]
                
                invalid_count = len(serializers) - len(valid_serializers)
                if invalid_count > 0:
                    print(f"Warning: {invalid_count} invalid leads in current batch")
                    logger.warning(f"{invalid_count} invalid leads in current batch")
                    if stats:
                        stats['failed'] += invalid_count
                
                if not valid_serializers:
                    print("Warning: No valid leads in current batch")
                    logger.warning("No valid leads in current batch")
                    return []
                
                # Create model instances without saving to database
                instances = []
                for serializer in valid_serializers:
                    try:
                        data_dict = dict(serializer.validated_data)
                        instance = Lead(**data_dict)
                        instances.append(instance)
                    except Exception as e:
                        print(f"Error creating lead instance: {str(e)}")
                        logger.error(f"Error creating lead instance: {str(e)}")
                        if stats:
                            stats['failed'] += 1
                
                try:
                    # Use bulk_create to insert all records in one go
                    lead_manager: Manager = Lead.objects  # type: ignore
                    saved_instances = lead_manager.bulk_create(instances, batch_size=100)
                    if stats:
                        stats['processed'] += len(saved_instances)
                    return saved_instances
                except Exception as e:
                    print(f"Error bulk saving leads: {str(e)}")
                    logger.error(f"Error bulk saving leads: {str(e)}")
                    if stats:
                        stats['failed'] += len(instances)
                    return []

            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    batch_instances = process_batch()
                    leads_instances.extend(batch_instances)
                    batch_time = time.time() - batch_start
                    print(f"Batch processed in {batch_time:.2f}s - Saved {len(batch_instances)} leads")
                    logger.info(f"Batch processed in {batch_time:.2f}s - Saved {len(batch_instances)} leads")
                    break  # Success, exit retry loop
                        
                except (OperationalError, IntegrityError, ValidationError) as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        print(f"Error: Max retries reached for leads batch. Error: {str(e)}")
                        logger.error(f"Max retries reached for leads batch. Error: {str(e)}")
                        raise
                    wait_time = (2 ** retry_count)  # Exponential backoff
                    print(f"Warning: Database operation failed, retrying in {wait_time} seconds...")
                    logger.warning(f"Database operation failed, retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    
        total_time = time.time() - batch_start
        print(f"\nFinished processing leads - Total time: {total_time:.2f}s - Processed: {len(leads_instances)}/{total_leads}")
        logger.info(f"Finished processing leads - Total time: {total_time:.2f}s - Processed: {len(leads_instances)}/{total_leads}")
        return leads_instances
                    
    except Exception as e:
        print(f"Error in process_leads_batch: {str(e)}")
        logger.error(f"Error in process_leads_batch: {str(e)}")
        raise

def process_appointments_batch(appointments_data: Optional[List[dict]] = None, stats: dict = None, batch_size: int = 1000) -> List[Appointment]:
    try:
        if not appointments_data:
            logger.warning("No appointments data to process")
            return []
            
        appointments_instances = []
        total_appointments = len(appointments_data)
        print(f"\nStarting to process {total_appointments} appointments in batches of {batch_size}")
        logger.info(f"Starting to process {total_appointments} appointments in batches of {batch_size}")
        
        for i in range(0, total_appointments, batch_size):
            batch = appointments_data[i:i + batch_size]
            batch_start = time.time()
            batch_end = min(i+batch_size, total_appointments)
            print(f"\nProcessing appointments batch {i+1}-{batch_end} of {total_appointments}")
            logger.info(f"Processing appointments batch {i+1}-{batch_end} of {total_appointments}")
            
            def process_batch() -> List[Appointment]:
                formatted_batch = [format_appointment_data(raw_appointment) for raw_appointment in batch]
                serializers = [AppointmentSerializer(data=data) for data in formatted_batch]
                valid_serializers = [s for s in serializers if s.is_valid()]
                
                invalid_count = len(serializers) - len(valid_serializers)
                if invalid_count > 0:
                    print(f"Warning: {invalid_count} invalid appointments in current batch")
                    logger.warning(f"{invalid_count} invalid appointments in current batch")
                    if stats:
                        stats['failed'] += invalid_count
                
                if not valid_serializers:
                    print("Warning: No valid appointments in current batch")
                    logger.warning("No valid appointments in current batch")
                    return []
                
                # Create model instances without saving to database
                instances = []
                for serializer in valid_serializers:
                    try:
                        data_dict = dict(serializer.validated_data)
                        instance = Appointment(**data_dict)
                        instances.append(instance)
                    except Exception as e:
                        print(f"Error creating appointment instance: {str(e)}")
                        logger.error(f"Error creating appointment instance: {str(e)}")
                        if stats:
                            stats['failed'] += 1
                
                try:
                    # Use bulk_create to insert all records in one go
                    appointment_manager: Manager = Appointment.objects  # type: ignore
                    saved_instances = appointment_manager.bulk_create(instances, batch_size=100)
                    if stats:
                        stats['processed'] += len(saved_instances)
                    return saved_instances
                except Exception as e:
                    print(f"Error bulk saving appointments: {str(e)}")
                    logger.error(f"Error bulk saving appointments: {str(e)}")
                    if stats:
                        stats['failed'] += len(instances)
                    return []

            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    batch_instances = process_batch()
                    appointments_instances.extend(batch_instances)
                    batch_time = time.time() - batch_start
                    print(f"Batch processed in {batch_time:.2f}s - Saved {len(batch_instances)} appointments")
                    logger.info(f"Batch processed in {batch_time:.2f}s - Saved {len(batch_instances)} appointments")
                    break  # Success, exit retry loop
                        
                except (OperationalError, IntegrityError, ValidationError) as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        print(f"Error: Max retries reached for appointments batch. Error: {str(e)}")
                        logger.error(f"Max retries reached for appointments batch. Error: {str(e)}")
                        raise
                    wait_time = (2 ** retry_count)  # Exponential backoff
                    print(f"Warning: Database operation failed, retrying in {wait_time} seconds...")
                    logger.warning(f"Database operation failed, retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    
        total_time = time.time() - batch_start
        print(f"\nFinished processing appointments - Total time: {total_time:.2f}s - Processed: {len(appointments_instances)}/{total_appointments}")
        logger.info(f"Finished processing appointments - Total time: {total_time:.2f}s - Processed: {len(appointments_instances)}/{total_appointments}")
        return appointments_instances
                    
    except Exception as e:
        print(f"Error in process_appointments_batch: {str(e)}")
        logger.error(f"Error in process_appointments_batch: {str(e)}")
        raise

def process_bill_charges_batch(bill_charges_data: Optional[List[dict]] = None, stats: dict = None, batch_size: int = 1000) -> List[BillCharge]:
    try:
        if not bill_charges_data:
            logger.warning("No bill charges data to process")
            return []
            
        bill_charges_instances = []
        total_bill_charges = len(bill_charges_data)
        print(f"\nStarting to process {total_bill_charges} bill charges in batches of {batch_size}")
        logger.info(f"Starting to process {total_bill_charges} bill charges in batches of {batch_size}")
        
        for i in range(0, total_bill_charges, batch_size):
            batch = bill_charges_data[i:i + batch_size]
            batch_start = time.time()
            batch_end = min(i+batch_size, total_bill_charges)
            print(f"\nProcessing bill charges batch {i+1}-{batch_end} of {total_bill_charges}")
            logger.info(f"Processing bill charges batch {i+1}-{batch_end} of {total_bill_charges}")
            
            def process_batch() -> List[BillCharge]:
                formatted_batch = [format_bill_charge_data(raw_bill_charge) for raw_bill_charge in batch]
                serializers = [BillChargeSerializer(data=data) for data in formatted_batch]
                valid_serializers = [s for s in serializers if s.is_valid()]
                
                invalid_count = len(serializers) - len(valid_serializers)
                if invalid_count > 0:
                    print(f"Warning: {invalid_count} invalid bill charges in current batch")
                    logger.warning(f"{invalid_count} invalid bill charges in current batch")
                    if stats:
                        stats['failed'] += invalid_count
                
                if not valid_serializers:
                    print("Warning: No valid bill charges in current batch")
                    logger.warning("No valid bill charges in current batch")
                    return []
                
                # Create model instances without saving to database
                instances = []
                for serializer in valid_serializers:
                    try:
                        data_dict = dict(serializer.validated_data)
                        instance = BillCharge(**data_dict)
                        instances.append(instance)
                    except Exception as e:
                        print(f"Error creating bill charge instance: {str(e)}")
                        logger.error(f"Error creating bill charge instance: {str(e)}")
                        if stats:
                            stats['failed'] += 1
                
                try:
                    # Use bulk_create to insert all records in one go
                    bill_charge_manager: Manager = BillCharge.objects  # type: ignore
                    saved_instances = bill_charge_manager.bulk_create(instances, batch_size=100)
                    if stats:
                        stats['processed'] += len(saved_instances)
                    return saved_instances
                except Exception as e:
                    print(f"Error bulk saving bill charges: {str(e)}")
                    logger.error(f"Error bulk saving bill charges: {str(e)}")
                    if stats:
                        stats['failed'] += len(instances)
                    return []

            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    batch_instances = process_batch()
                    bill_charges_instances.extend(batch_instances)
                    batch_time = time.time() - batch_start
                    print(f"Batch processed in {batch_time:.2f}s - Saved {len(batch_instances)} bill charges")
                    logger.info(f"Batch processed in {batch_time:.2f}s - Saved {len(batch_instances)} bill charges")
                    break  # Success, exit retry loop
                        
                except (OperationalError, IntegrityError, ValidationError) as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        print(f"Error: Max retries reached for bill charges batch. Error: {str(e)}")
                        logger.error(f"Max retries reached for bill charges batch. Error: {str(e)}")
                        raise
                    wait_time = (2 ** retry_count)  # Exponential backoff
                    print(f"Warning: Database operation failed, retrying in {wait_time} seconds...")
                    logger.warning(f"Database operation failed, retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    
        total_time = time.time() - batch_start
        print(f"\nFinished processing bill charges - Total time: {total_time:.2f}s - Processed: {len(bill_charges_instances)}/{total_bill_charges}")
        logger.info(f"Finished processing bill charges - Total time: {total_time:.2f}s - Processed: {len(bill_charges_instances)}/{total_bill_charges}")
        return bill_charges_instances
                    
    except Exception as e:
        print(f"Error in process_bill_charges_batch: {str(e)}")
        logger.error(f"Error in process_bill_charges_batch: {str(e)}")
        raise

def assemble_all_data(leads_instances: List[Lead], appointments_instances: List[Appointment], bill_charges_instances: List[BillCharge]) -> Optional[AllDataType]:
    try:
        data = {
            'leads': leads_instances or [],
            'appointments': appointments_instances or [],
            'bill_charges': bill_charges_instances or []
        }
        return AllDataType(**data)
    except Exception as e:
        logger.error(f"Error assembling all data: {str(e)}")
        return None