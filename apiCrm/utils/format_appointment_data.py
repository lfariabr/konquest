def format_appointment_data(raw_appointment):
    # Ensure raw_appointment is a dictionary
    if raw_appointment is None:
        raw_appointment = {}
        
    # Get nested values safely
    status = raw_appointment.get('status')
    status = status if isinstance(status, dict) else {}
    
    store = raw_appointment.get('store')
    store = store if isinstance(store, dict) else {}
    
    customer = raw_appointment.get('customer')
    customer = customer if isinstance(customer, dict) else {}
    
    telephones = customer.get('telephones', [])
    telephones = telephones if isinstance(telephones, list) else []
    first_telephone = telephones[0] if telephones else {}
    first_telephone = first_telephone if isinstance(first_telephone, dict) else {}
    
    procedure = raw_appointment.get('procedure')
    procedure = procedure if isinstance(procedure, dict) else {}
    
    employee = raw_appointment.get('employee')
    employee = employee if isinstance(employee, dict) else {}
    
    created_by = raw_appointment.get('createdBy')
    created_by = created_by if isinstance(created_by, dict) else {}
    
    return {
        'id_crm': raw_appointment.get('id', 'N/A'),
        'status_label': status.get('label', 'N/A'),
        'store_name': store.get('name', 'N/A'),
        'customer_id': customer.get('id', 'N/A'),
        'customer_name': customer.get('name', 'N/A'),
        'customer_phone': first_telephone.get('number', 'N/A'),
        'procedure_name': procedure.get('name', 'N/A'),
        'procedure_group': procedure.get('groupLabel', 'N/A'),
        'employee_name': employee.get('name', 'N/A'),
        'createdby_name': created_by.get('name', 'N/A'),
        'createdby_created_at': created_by.get('createdAt', 'N/A'),
        'appointment_date': raw_appointment.get('startDate', 'N/A'),
    }