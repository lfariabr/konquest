from django.contrib import admin
from .models.file_message import FileMessage
from .models.text_message import TextMessage
from .resolvers.send_file_message import send_file_message
from .resolvers.send_text_message import send_text_message

@admin.register(TextMessage)
class TextMessageAdmin(admin.ModelAdmin):
    list_display = ('phone', 'message', 'status', 'response')
    actions = ['send_text_message_action']

    def send_text_message_action(self, request, queryset):
        for text_message in queryset:
            response = send_text_message(
                phone=text_message.phone,
                message=text_message.message,
                token_socialhub='rmvYoOnWD5WjcH7Bx5lYTZkGMX2vweN1',
            )
            text_message.status = 'Sent' if response.get('success') else 'Failed'
            text_message.response = response
            text_message.save()
        self.message_user(request, "Text message(s) sent successfully!")

    send_text_message_action.short_description = "Send selected text messages"

@admin.register(FileMessage)
class FileMessageAdmin(admin.ModelAdmin):
    list_display = ('phone', 'message', 'file', 'status')
    actions = ['send_file_message_action']

    def send_file_message_action(self, request, queryset):
        for file_message in queryset:
            response = send_file_message(
                phone=file_message.phone,
                message=file_message.message,
                token_socialhub='rmvYoOnWD5WjcH7Bx5lYTZkGMX2vweN1',
                file_path=file_message.file.path,
            )
            file_message.status = 'Sent' if response.get('success') else 'Failed'
            file_message.response = response
            file_message.save()
        self.message_user(request, "File message(s) sent successfully!")

    send_file_message_action.short_description = "Send selected file messages"