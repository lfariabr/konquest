# Introduction
We are facing a situation where multiple contacts are being created for the same customer, saving this specific customer in different tags.

This is a problem because when we are about to process the target_list at @target_list_resolver, we are not checking anything to prioritize the contacts.

Furthermore, to make matters worse, when we @get_contact_appointment, we are doing a bunch complicated logic with different base queries to get the right contact, none of them taking into account the priority.

# Solution:
1. Create a flag at Contact.py called "available_to_queue" which will be a boolean
2. Create a flag at Contact.py called "priority" which will be an integer (1, 2, 3, 4, 5), based on the contact_tag
3. At target_list_resolver, when about to put a contact in the target_list, check if available_to_queue is True and check if priority is 1
4. If NO, skip the contact. If YES, move forward and process the contact.

# Enhancements at get_contact_appointment

First of all, we need to have a base query to get the appointment with the desired info:
reschedule_appointment_query
reminder_appointment_query
nps_appointment_query

Then, we need to exclude potential unwanted contacts from these queries.
reminder_appointment_query is priority. we don't need to exclude nothing from it.
reschedule_appointment_query we need to exclude future appointments (that are here: reminder_appointment_query)
nps_appointment_query we don't need to exclude anything, it already sends one message to the contact and never anymore.

# Implementation
## contacts.py
Added these fields after the user field:
- available_to_queue = models.BooleanField(default=True, help_text="Whether this contact is available for queue processing")
- priority = models.IntegerField(default=5, help_text="Contact priority (1-5, where 1 is highest priority)")

## get_contact_appointment.py
- created specific functions for each query
- implemented at least one of them: get_reschedule_appointment_query to test
- refacterd all functions to get contacts moving it to a helper folder at @appointment_queries.py

## target_list_resolver.py
- Added this:  contacts = [c for c in contacts if c.available_to_queue and c.priority == 5]

# Pending:
- think about logic to update PRIORITY of the contact and use this on the target list