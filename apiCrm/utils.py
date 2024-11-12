from .serializers import LeadSerializer, AppointmentSerializer, BillChargeSerializer

def format_lead_data(raw_lead):
    return {
        'id_crm': raw_lead['id'],
        'name': raw_lead['name'],
        'email': raw_lead['email'],
        'phone': raw_lead['telephone'],
        'source': raw_lead['source']['title'],
        'store': raw_lead['store']['name'] if raw_lead.get('store') else None,
        'status': raw_lead['status']['label'],
        'customer_id': raw_lead['customer']['id'] if raw_lead.get('customer') else None,
        'created_at': raw_lead['createdAt'],
        'utm_medium': raw_lead.get('utmMedium'),
        'utm_campaign': raw_lead.get('utmCampaign'),
        'utm_content': raw_lead.get('utmContent'),
        'utm_search': raw_lead.get('utmSearch'),
        'utm_term': raw_lead.get('utmTerm'),
        'message': raw_lead.get('message')
    }

def format_appointment_data(raw_appointment):
    return {
        'id_crm': raw_appointment['id'],
        'status_label': raw_appointment['status']['label'],
        'store_name': raw_appointment['store']['name'],
        'customer_id': raw_appointment['customer']['id'],
        'customer_name': raw_appointment['customer']['name'],
        'customer_phone': raw_appointment['customer'].get('telephones', [{}])[0].get('number', 'N/A'),
        'procedure_name': raw_appointment.get('procedure', {}).get('name', 'N/A'),
        'procedure_group': raw_appointment.get('procedure', {}).get('groupLabel', 'N/A'),
        'employee_name': raw_appointment.get('employee', {}).get('name', 'N/A'),
        'createdby_name': raw_appointment.get('createdBy', {}).get('name', 'N/A'),
        'createdby_created_at': raw_appointment.get('createdBy', {}).get('createdAt'),
        'appointment_date': raw_appointment['startDate'],
    }

def format_bill_charge_data(raw_bill_charge):
    quote = raw_bill_charge['quote']
    return {
        'quote_id': quote['id'],
        'customer_id': quote['customer']['id'],
        'customer_name': quote['customer']['name'],
        'customer_taxvat': quote['customer'].get('taxvat', 'N/A'),
        'customer_email': quote['customer'].get('email', ''),
        'store_name': raw_bill_charge['store']['name'],
        'total_amount': quote['bill']['total'],
        'installments': quote['bill'].get('installmentsQuantity', 'N/A'),
        'paid_at': raw_bill_charge.get('paidAt', 'N/A'),
        'due_at': raw_bill_charge.get('dueAt', 'N/A'),
        'is_paid': raw_bill_charge['isPaid'],
        'payment_method': raw_bill_charge['paymentMethod']['name'],
        'status': quote['status'],
        'quote_items': "; ".join([f"{item['description']} (Qty: {item['quantity']}, Amount: {item['amount']})" for item in quote['bill']['items']])
    }

def process_and_save_leads(leads_data):
    leads_list = []
    for raw_lead in leads_data:
        formatted_lead = format_lead_data(raw_lead)
        serializer = LeadSerializer(data=formatted_lead)
        if serializer.is_valid():
            serializer.save()
            leads_list.append(LeadType(**serializer.validated_data))
        else:
            print(f"Failed to save lead: {serializer.errors}")
    return leads_list

def process_and_save_appointments(appointments_data):
    appointments_list = []
    for raw_appointment in appointments_data:
        formatted_appointment = format_appointment_data(raw_appointment)
        serializer = AppointmentSerializer(data=formatted_appointment)
        if serializer.is_valid():
            serializer.save()
            appointments_list.append(AppointmentType(**serializer.validated_data))
        else:
            print(f"Failed to save appointment: {serializer.errors}")
    return appointments_list

def process_and_save_bill_charges(bill_charges_data):
    bill_charges_list = []
    for raw_bill_charge in bill_charges_data:
        formatted_bill_charge = format_bill_charge_data(raw_bill_charge)
        serializer = BillChargeSerializer(data=formatted_bill_charge)
        if serializer.is_valid():
            serializer.save()
            bill_charges_list.append(BillChargeType(**serializer.validated_data))
        else:
            print(f"Failed to save bill charge: {serializer.errors}")
    return bill_charges_list