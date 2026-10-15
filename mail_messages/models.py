from django.contrib.auth.models import User
from django.db import models


class Message(models.Model):
    """Модель сообщения для рассылки."""

    subject: models.CharField = models.CharField(
        max_length=255,
        verbose_name="Тема письма",
        help_text="Введите тему письма",
    )
    body: models.TextField = models.TextField(
        verbose_name="Тело письма",
        help_text="Введите содержание письма",
    )
    owner: models.ForeignKey = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Владелец",
        related_name="messages",
        help_text="Пользователь, создавший сообщение",
    )
    created_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )
    updated_at: models.DateTimeField = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления",
    )

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.subject
