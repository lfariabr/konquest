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

main_urlpatterns = [
    path('admin/', admin_site.urls),
    path('apiCrm/', include('apiCrm.urls')),
]

urlpatterns = [
    path('', views.home, name='home'),
    path('', include(main_urlpatterns)),
    path('apiCrm/graphql/', GraphQLView.as_view(graphiql=True, schema=schema)),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'img/favicon.svg', permanent=True)),

]

if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]
    
    # Serve media and static files in development mode
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)