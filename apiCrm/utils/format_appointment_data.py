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