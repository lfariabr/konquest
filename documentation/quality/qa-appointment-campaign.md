# Quality Assurance - Appointment Campaign

## Introduction
The task of generating target lists will run everyday. This task is crucial because daily the list will change and with it, clients to be contacted according to the campaign's rules.

We created something beautiful with campaign type Whatsapp. However, at Appointments, we had to be a little bit bold.
We had to take the rules from @is_appointment_es.py, filter the clients and create them as Contacts. After creating them as contacts, we can add them to the TargetList without problems and move forward on the sequence of processing the Queue and delivering custom messages.

I'm being cautious here and a concern has been tormeting my thoughts. I'm bit confused if there would be issues to replacing existing data on the main part of the system: "Contacts.py".

# Possible Edge Cases
1. Client ID 1 is appointment "Reminder" today, created as Contact and receive message day 1. At day 2, client 1 is still an appointment under "Reminder" tag and already a client. Will there be any problem in generating the Target List and processing the Queue?
    ### R: When client appears again for same campaign (e.g., "Reminder")
    @get_appointment_to_contact.py got this covered:
    existing_contact = Contact.objects.filter(
        phone=appointment.customer_phone,
        relationship_tag=contact_tag  # Same tag = update existing contact
    ).first()
    - The same contact will be found and updated
    - The appointment_status and appointment_id are updated
    - No duplicate is created

2. Client ID 1 is Whatsapp lead, which is top funnel. When client enter as an appointment and as a "reminder" campaign, if he's already a contact, will he be added to target list and receive message day 1?
    ### R: Different relationship_tag = new contact created
    @get_appointment_to_contact.py got this covered:
    contact = Contact(
        phone=appointment.customer_phone,
        relationship_tag=contact_tag,  # New tag = new contact
        source='Appointment'
    )
    - A new contact is created with appointment source
    - The original Whatsapp contact remains unchanged
    - Both campaigns can run independently

3. Other possible cases?

