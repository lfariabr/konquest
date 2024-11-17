# apiCrm/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('leads/', views.leads_view, name='leads'),
    path('appointments/', views.appointments_view, name='appointments'),
    path('bill-charges/', views.bill_charges_view, name='bill-charges'),
]