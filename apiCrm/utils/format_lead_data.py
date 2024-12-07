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