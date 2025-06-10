from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.viewsets.contact_viewset import ContactViewSet
from api.viewsets.messagelog_viewset import MessageLogsViewSet

router = DefaultRouter()
router.register(r'contacts', ContactViewSet, basename='contacts')
router.register(r'messagelogs', MessageLogsViewSet, basename='messagelogs')

urlpatterns = [
    path('', include(router.urls)),
]
