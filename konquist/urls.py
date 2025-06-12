# konquista/urls.py
from . import views
from .admin import admin_site
from django.conf import settings
from django.urls import reverse
from django.urls import path, include
from django.conf.urls.static import static
from graphene_django.views import GraphQLView
from django.views.generic.base import RedirectView
from apiCrm.schemas.resolve_all_data import schema
from django.views.generic import TemplateView
from utils.discord import connect_clicked
from api.urls import urlpatterns as api_urlpatterns
from django.views.decorators.csrf import csrf_exempt
from api.schema import schema_graphene
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

main_urlpatterns = [
    path('admin/', admin_site.urls),
    path('apiCrm/', include('apiCrm.urls')),
    
    # api layer - django rest framework
    path('api/', include(api_urlpatterns)),
    
    # Discord webhook
    path('api/notify-connect-click/', connect_clicked, name='discord_connect_clicked'),
    
    # JWT Token endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

urlpatterns = [
    path('', views.home, name='home'),
    path('', include(main_urlpatterns)),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'img/favicon.svg', permanent=True)),

    # graphene to play with apiCrm
    path('apiCrm/graphql/', GraphQLView.as_view(graphiql=True, schema=schema)),
    
    # api layer - graphene
    # path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema_graphene))),
]

if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]
    
    # Serve media and static files in development mode
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)