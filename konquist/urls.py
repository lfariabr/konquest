# konquista/urls.py
from django.contrib import admin
from django.urls import path, include
from apiCrm.schemas.resolve_all_data import schema
from graphene_django.views import GraphQLView
from . import views
from .admin import admin_site
from django.views.generic.base import RedirectView
from django.templatetags.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin_site.urls),
    path('apiCrm/graphql/', GraphQLView.as_view(graphiql=True, schema=schema)),
    path('apiCrm/', include('apiCrm.urls')),
    path('favicon.ico', RedirectView.as_view(url=static('img/favicon.svg'), permanent=True)),
]