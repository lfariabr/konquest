# Message Logs Table
## Legacy SQL Message Logs Structure to migrate
legacy_message_logs_columns = [id, message_id, sender_phone_id, sender_phone_number, source, lead_phone_id, lead_phone_number, date_sent, status, message_text, message_title, user_id]

## New Message Logs Structure
current_message_logs_columns = [
    message: message.text,
    user: user_id,
    user_phone: sender_phone_number,
    contact: lead_phone_number,
    status: status,
    sent_at: date_sent,
    relationship_tag: ? (it could be the user_phone, because 1 phone = 1 relationship_tag)
]

# Contact Table
## Legacy SQL Contact Structure to migrate
legacy_contact_columns = [
    id: ?,
    phone: phone,
    name: name,
    created_date,
    tag: relationship_tag,
    source: source,
    store: store,
    region: region,
    tags: external_tag,
    user_id: ?
    ]

## New Contact Structure
current_contact_columns = [
    name,
    phone,
    created_at,
    relationship_tag,
    source,
    store,
    region,
    user,

    # external info, crm
    reference_code,
    external_tag,
    tag,
    status,

    # lead checking
    is_lead,
    lead_id,
    lead_status,
    lead_created_at,
    lead_last_checked,
    lead_check_count,
    store_lead,

    # appointment checking
    is_appointment,
    appointment_id,
    appointment_status,
    appointment_created_at,
    appointment_last_checked,
    appointment_check_count,
    store_appointment,

    # buyer checking - not yet implemented
    is_buyer,
    buyer_id,
    buyer_status,
    buyer_created_at,
    buyer_last_checked,
    buyer_check_count,
    store_buyer
]

# Last updates:
Terminal: 
python manage.py shell
>>> from core.models.data_import import run_import
>>> run_import()

Terminal:
python manage.py shell
>>> from core.models.message_log_import import run_import
>>> run_import()