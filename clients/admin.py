from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Админ-панель для модели Client."""

    list_display = ("full_name", "email", "owner", "created_at")
    list_filter = ("created_at", "owner")
    search_fields = ("full_name", "email", "comment")
    readonly_fields = ("created_at", "updated_at")
