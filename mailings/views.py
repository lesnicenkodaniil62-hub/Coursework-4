from typing import Any, cast

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from mail_messages.models import Message
from users.mixins import OwnerFilterMixin

from .forms import MailingForm
from .models import Mailing, MailingAttempt


class MailingListView(LoginRequiredMixin, OwnerFilterMixin, ListView):
    """Список всех рассылок текущего пользователя."""

    model = Mailing
    template_name = "mailings/mailing_list.html"
    context_object_name = "mailings"
    paginate_by = 10


class MailingDetailView(LoginRequiredMixin, OwnerFilterMixin, DetailView):
    """Детальная информация о рассылке."""

    model = Mailing
    template_name = "mailings/mailing_detail.html"
    context_object_name = "mailing"

    def get_object(self, queryset: QuerySet[Mailing] | None = None) -> Mailing:
        """Переопределяем для вызова update_status()."""
        obj = super().get_object(queryset)
        obj.update_status()
        return obj


class MailingCreateView(LoginRequiredMixin, CreateView):
    """Создание новой рассылки."""

    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"
    success_url = reverse_lazy("mailings:mailing_list")

    def get_form_kwargs(self) -> dict[str, Any]:
        """Передаём пользователя в форму."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form: MailingForm) -> Any:
        """Устанавливает владельца перед сохранением."""
        user = cast(User, self.request.user)
        form.instance.owner = user
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, OwnerFilterMixin, UpdateView):
    """Редактирование рассылки."""

    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"
    success_url = reverse_lazy("mailings:mailing_list")

    def get_form_kwargs(self) -> dict[str, Any]:
        """Передаём пользователя в форму."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class MailingDeleteView(LoginRequiredMixin, OwnerFilterMixin, DeleteView):  # type: ignore[misc]
    """Удаление рассылки."""

    model = Mailing
    template_name = "mailings/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailings:mailing_list")


class MailingSendView(LoginRequiredMixin, View):
    """Запуск рассылки вручную."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Обрабатывает POST-запрос для запуска рассылки."""
        user = cast(User, request.user)
        mailing = get_object_or_404(Mailing, pk=pk, owner=user)

        mailing.update_status()

        if mailing.status != Mailing.STATUS_RUNNING:
            status_display = mailing.get_status_display()  # type: ignore[attr-defined]
            error_message = (
                f"Рассылка не может быть запущена. Текущий статус: {status_display}. "
                "Отправка разрешена только для активных рассылок."
            )
            messages.error(request, error_message)
            return redirect("mailings:mailing_detail", pk=pk)

        now = timezone.now()
        if not (mailing.start_time <= now <= mailing.end_time):
            messages.error(request, "Текущее время находится вне разрешённого окна отправки.")
            return redirect("mailings:mailing_detail", pk=pk)

        recipients = mailing.recipients.all()
        if not recipients.exists():
            messages.warning(request, "У рассылки нет получателей.")
            return redirect("mailings:mailing_detail", pk=pk)

        message_obj = cast(Message, mailing.message)

        attempts_data = []
        success_count = 0
        fail_count = 0

        for client in recipients:
            try:
                send_mail(
                    subject=message_obj.subject,
                    message=message_obj.body,
                    from_email=None,
                    recipient_list=[client.email],
                    fail_silently=False,
                )
                attempts_data.append(
                    MailingAttempt(
                        mailing=mailing,
                        status=MailingAttempt.STATUS_SUCCESS,
                        server_response="Письмо успешно отправлено",
                    )
                )
                success_count += 1
            except Exception as e:
                attempts_data.append(
                    MailingAttempt(
                        mailing=mailing,
                        status=MailingAttempt.STATUS_FAILED,
                        server_response=str(e),
                    )
                )
                fail_count += 1

        MailingAttempt.objects.bulk_create(attempts_data)

        messages.success(request, f"Рассылка завершена. Успешно: {success_count}, Ошибок: {fail_count}.")

        return redirect("mailings:mailing_detail", pk=pk)
