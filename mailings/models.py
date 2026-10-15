from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from clients.models import Client
from mail_messages.models import Message


class Mailing(models.Model):
    """Модель рассылки."""

    STATUS_CREATED = "created"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"

    STATUS_CHOICES = [
        (STATUS_CREATED, "Создана"),
        (STATUS_RUNNING, "Запущена"),
        (STATUS_COMPLETED, "Завершена"),
    ]

    start_time = models.DateTimeField(
        verbose_name="Дата и время начала отправки",
        help_text="С какого момента рассылка может быть запущена",
    )
    end_time = models.DateTimeField(
        verbose_name="Дата и время окончания отправки",
        help_text="До какого момента разрешено выполнять отправку",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_CREATED,
        verbose_name="Статус",
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        verbose_name="Сообщение",
        related_name="mailings",
        help_text="Какое письмо будет отправлено в рассылке",
    )
    recipients = models.ManyToManyField(
        Client,
        verbose_name="Получатели",
        related_name="mailings",
        help_text="Список клиентов, которые получат данную рассылку",
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Владелец",
        related_name="mailings",
        help_text="Пользователь, создавший рассылку",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления",
    )

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Рассылка #{self.pk} ({self.get_status_display()})"

    def clean(self) -> None:
        """Валидация дат."""
        super().clean()
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError({"end_time": "Дата окончания должна быть позже даты начала."})

    def update_status(self) -> None:
        """Обновляет статус рассылки на основе текущего времени."""
        now = timezone.now()
        if now < self.start_time:
            new_status = self.STATUS_CREATED
        elif self.start_time <= now <= self.end_time:
            new_status = self.STATUS_RUNNING
        else:
            new_status = self.STATUS_COMPLETED

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=["status", "updated_at"])


class MailingAttempt(models.Model):
    """Модель попытки отправки письма."""

    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Успешно"),
        (STATUS_FAILED, "Не успешно"),
    ]

    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        verbose_name="Рассылка",
        related_name="attempts",
        help_text="Рассылка, к которой относится попытка",
    )
    attempt_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время попытки",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name="Статус",
    )
    server_response = models.TextField(
        blank=True,
        null=True,
        verbose_name="Ответ почтового сервера",
        help_text="Текст ответа или ошибки",
    )

    class Meta:
        verbose_name = "Попытка отправки"
        verbose_name_plural = "Попытки отправки"
        ordering = ["-attempt_time"]

    def __str__(self) -> str:
        return f"Попытка #{self.pk} для рассылки #{self.mailing_id} ({self.get_status_display()})"
