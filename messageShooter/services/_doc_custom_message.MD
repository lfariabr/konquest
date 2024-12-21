Let's stop and think for a moment.
The current problem we're trying to solve on this branch is the CUSTOM MESSAGE thing.
We already can send messages to all different types of target lists, whether the campaign is Whatsapp or Appointments, are you following with me?

Now, the problem is that the variables I want to use on the message should be able to replace the [] things as expressed at @get_message_for_contact.py :
"Olá [nome]! 😊 
Seu agendamento na [unidade] é hoje!
⏰ Horário: [hora]
📍 Endereço: [address]"

I know that we have both NAME and STORE from the contact list, so let's first, try to fix it, shall we?
Where exactly should we use/adapt the GET MESSAGE to use?
If I'm not mistaken, it is in the queue processor that we get each message for each person that will receive a message.

Aside from that, and thinking about the future, We ideally also need to think about being able to access more than the current variables we have available from Contact model, for example:

all the replacements that are on @customize_message_text ...
These fields are not necessarily at the Contact model, but they for sure are on the Appointment model which originates these contacts at @get_contacts.py 

options that I thought to solve it:
1. create these fields in contact model as null=True and store these specific data for usage
2. new class ContactAppointment to store this data
3. temporary hashmap dict with this data
4. Redis in memory solution

How can we solve this situation? Please enlighten me.