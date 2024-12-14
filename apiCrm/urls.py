# apiCrm/urls.py

from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from . import views
from .schemas.resolve_all_data import schema

urlpatterns = [
    path('leads/', views.leads_view, name='leads'),
    path('appointments/', views.appointments_view, name='appointments'),
    path('bill-charges/', views.bill_charges_view, name='bill-charges'),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))),
]