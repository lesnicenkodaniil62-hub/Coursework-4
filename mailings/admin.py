from django.contrib import admin

from .models import Mailing, MailingAttempt


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    """Админ-панель для модели Mailing."""

    list_display = ("pk", "status", "message", "start_time", "end_time", "owner", "created_at")
    list_filter = ("status", "created_at", "owner")
    search_fields = ("message__subject",)
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("recipients",)


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    """Админ-панель для модели MailingAttempt."""

    list_display = ("pk", "mailing", "status", "attempt_time")
    list_filter = ("status", "attempt_time")
    readonly_fields = ("attempt_time",)
