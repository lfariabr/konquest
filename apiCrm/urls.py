# apiCrm/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Defina aqui quaisquer outras rotas específicas do apiCrm, como:
    path('leads/', views.leads_view, name='leads_view'),  # Exemplo de URL específica para leads
    # Outras rotas de views específicas do app podem ser adicionadas aqui
]