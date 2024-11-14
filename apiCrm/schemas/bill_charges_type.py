from graphene_django.types import DjangoObjectType
import graphene

class BillChargeType(graphene.ObjectType):
    id = graphene.String()  # Define `id` field for GraphQL
    quote_id = graphene.String()
    customer_id = graphene.String()
    customer_name = graphene.String()
    customer_taxvat = graphene.String()
    customer_email = graphene.String()
    store_name = graphene.String()
    total_amount = graphene.Float()
    installments = graphene.Int()
    paid_at = graphene.String()
    due_at = graphene.String()
    is_paid = graphene.Boolean()
    payment_method = graphene.String()
    status = graphene.String()
    quote_items = graphene.String()

    def resolve_id(self, info):
        return self.quote_id  # Return `quote_id` as `id` in the GraphQL response