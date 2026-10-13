from django.apps import AppConfig


class MailMessagesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mail_messages"
    verbose_name = "Сообщения для рассылок"
