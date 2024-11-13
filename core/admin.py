from django.contrib import admin
from core.models.user import User
from core.models.contact import Contact
from core.models.userphone import UserPhone
from core.models.message import Message
from core.models.messagelog import MessageLogs

class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'user', 'relationship_tag', 'source', 'store', 'region', 'reference_code', 'external_tag')
    search_fields = ('name', 'phone', 'user__name')
    list_filter = ('name', 'phone', 'user', 'relationship_tag', 'source', 'store', 'region')
    ordering = ['-created_at']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

admin.site.register(Contact, ContactAdmin)

class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'company')
    search_fields = ('name', 'email', 'company')
    list_filter = ('company',)
    ordering = ['-created_at']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

admin.site.register(User, UserAdmin)

class UserPhoneAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'user', 'phone_token', 'phone_description')
    search_fields = ('phone_number', 'user__name')
    list_filter = ('user', 'phone_description')
    ordering = ['-created_at']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

admin.site.register(UserPhone, UserPhoneAdmin)

class MessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'text', 'file_type')
    search_fields = ('user__name', 'title', 'text')
    list_filter = ('user', 'title', 'text')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

admin.site.register(Message, MessageAdmin)

class MessageLogsAdmin(admin.ModelAdmin):
    list_display = ('message', 'user', 'user_phone', 'contact', 'sent_at')
    search_fields = ('message__title', 'user__name', 'user_phone__phone_number', 'contact__name')
    list_filter = ('sent_at', 'user', 'user_phone', 'contact')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

admin.site.register(MessageLogs, MessageLogsAdmin)