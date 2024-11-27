from django.apps import AppConfig


class MessageshooterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'messageShooter'
    
    def ready(self):
        import messageShooter.signals  # noqa
