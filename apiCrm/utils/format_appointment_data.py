def format_appointment_data(raw_appointment):
    return {
        'id_crm': raw_appointment.get('id', 'N/A'),
        'status_label': raw_appointment.get('status', {}).get('label', 'N/A'),
        'store_name': raw_appointment.get('store', {}).get('name', 'N/A'),
        'customer_id': raw_appointment.get('customer', {}).get('id', 'N/A'),
        'customer_name': raw_appointment.get('customer', {}).get('name', 'N/A'),
        'customer_phone': (
            raw_appointment.get('customer', {}).get('telephones', [{}])[0].get('number', 'N/A')
            if raw_appointment.get('customer', {}).get('telephones') else 'N/A'
        ),
        'procedure_name': raw_appointment.get('procedure', {}).get('name', 'N/A'),
        'procedure_group': raw_appointment.get('procedure', {}).get('groupLabel', 'N/A'),
        'employee_name': raw_appointment.get('employee', {}).get('name', 'N/A'),
        'createdby_name': raw_appointment.get('createdBy', {}).get('name', 'N/A'),
        'createdby_created_at': raw_appointment.get('createdBy', {}).get('createdAt', 'N/A'),
        'appointment_date': raw_appointment.get('startDate', 'N/A'),
    }