from django.contrib import admin

from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Админ-панель для модели Message."""

    list_display = ("subject", "owner", "created_at")
    list_filter = ("created_at", "owner")
    search_fields = ("subject", "body")
    readonly_fields = ("created_at", "updated_at")
