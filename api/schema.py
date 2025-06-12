# API layer - graphene
# Currently not being used

import graphene
from graphene_django import DjangoObjectType
from core.models.contact import Contact
from core.models.messagelog import MessageLogs

class ContactType(DjangoObjectType):
    class Meta:
        model = Contact
        fields = "__all__"
        interfaces = (graphene.relay.Node,)

class MessageLogType(DjangoObjectType):
    class Meta:
        model = MessageLogs
        fields = "__all__"
        interfaces = (graphene.relay.Node,)

class Query(graphene.ObjectType):
    all_contacts = graphene.List(ContactType)
    contact = graphene.Field(ContactType, id=graphene.Int())
    all_message_logs = graphene.List(MessageLogType)
    
    def resolve_all_contacts(self, info, **kwargs):
        return Contact.objects.all()
    
    def resolve_contact(self, info, id):
        return Contact.objects.get(pk=id)
    
    def resolve_all_message_logs(self, info, **kwargs):
        return MessageLogs.objects.all()

class CreateContact(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        phone = graphene.String(required=True)
        # Add other fields as needed
    
    contact = graphene.Field(ContactType)
    
    def mutate(self, info, name, phone):
        contact = Contact(name=name, phone=phone)
        contact.save()
        return CreateContact(contact=contact)

class Mutation(graphene.ObjectType):
    create_contact = CreateContact.Field()

schema_graphene = graphene.Schema(query=Query, mutation=Mutation)

# Examples
## Get contacts
# {
#   allContacts {
#     id
#     name
#     phone
#   }
# }

## Create contact
# mutation {
#   createContact(input: {name: "John Doe", phone: "1234567890"}) {
#     contact {
#       id
#       name
#       phone
#     }
#   }
# }

