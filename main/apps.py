from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "main"
    verbose_name = "Главная страница и статистика"

    def ready(self) -> None:
        from .signals import register_dashboard_signals

        register_dashboard_signals()
