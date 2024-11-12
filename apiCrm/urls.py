# apiCrm/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('leads/', views.leads_view, name='leads_view'),
    path('appointments/', views.appointments_view, name='appointments_view'),
    path('bill_charges/', views.bill_charges_view, name='bill_charges_view'),
]