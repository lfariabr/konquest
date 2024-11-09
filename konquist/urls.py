# konquista/urls.py
from django.contrib import admin
from django.urls import path, include
from apiCrm.schema import schema
from graphene_django.views import GraphQLView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('apiCrm/graphql/', GraphQLView.as_view(graphiql=True, schema=schema)),  # graphql view
    path('apiCrm/', include('apiCrm.urls')), # Django Rest Framework view Leads
]