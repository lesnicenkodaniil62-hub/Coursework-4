from typing import Any, cast

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import MailingForm
from .models import Mailing


class MailingListView(LoginRequiredMixin, ListView):
    """Список всех рассылок текущего пользователя."""

    model = Mailing
    template_name = "mailings/mailing_list.html"
    context_object_name = "mailings"
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Mailing]:
        """Возвращает только рассылки текущего пользователя."""
        user = cast(User, self.request.user)
        return Mailing.objects.filter(owner=user)


class MailingDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о рассылке."""

    model = Mailing
    template_name = "mailings/mailing_detail.html"
    context_object_name = "mailing"

    def get_queryset(self) -> QuerySet[Mailing]:
        """Возвращает только рассылки текущего пользователя."""
        user = cast(User, self.request.user)
        return Mailing.objects.filter(owner=user)

    def get_object(self, queryset: QuerySet[Mailing] | None = None) -> Mailing:
        """Переопределяем для вызова update_status()."""
        obj = super().get_object(queryset)
        obj.update_status()  # ← пересчёт и сохранение статуса
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


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование рассылки."""

    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"
    success_url = reverse_lazy("mailings:mailing_list")

    def get_queryset(self) -> QuerySet[Mailing]:
        """Возвращает только рассылки текущего пользователя."""
        user = cast(User, self.request.user)
        return Mailing.objects.filter(owner=user)

    def get_form_kwargs(self) -> dict[str, Any]:
        """Передаём пользователя в форму."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление рассылки."""

    model = Mailing
    template_name = "mailings/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailings:mailing_list")

    def get_queryset(self) -> QuerySet[Mailing]:
        """Возвращает только рассылки текущего пользователя."""
        user = cast(User, self.request.user)
        return Mailing.objects.filter(owner=user)
