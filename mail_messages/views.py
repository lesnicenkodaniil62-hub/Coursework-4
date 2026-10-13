from typing import Any, cast

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import MessageForm
from .models import Message


class MessageListView(LoginRequiredMixin, ListView):
    """Список всех сообщений текущего пользователя."""

    model = Message
    template_name = "mail_messages/message_list.html"
    context_object_name = "messages"
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Message]:
        """Возвращает только сообщения текущего пользователя."""
        user = cast(User, self.request.user)
        return Message.objects.filter(owner=user)


class MessageDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о сообщении."""

    model = Message
    template_name = "mail_messages/message_detail.html"
    context_object_name = "message"

    def get_queryset(self) -> QuerySet[Message]:
        """Возвращает только сообщения текущего пользователя."""
        user = cast(User, self.request.user)
        return Message.objects.filter(owner=user)


class MessageCreateView(LoginRequiredMixin, CreateView):
    """Создание нового сообщения."""

    model = Message
    form_class = MessageForm
    template_name = "mail_messages/message_form.html"
    success_url = reverse_lazy("mail_messages:message_list")

    def form_valid(self, form: MessageForm) -> Any:
        """Устанавливает владельца перед сохранением."""
        user = cast(User, self.request.user)
        form.instance.owner = user
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование сообщения."""

    model = Message
    form_class = MessageForm
    template_name = "mail_messages/message_form.html"
    success_url = reverse_lazy("mail_messages:message_list")

    def get_queryset(self) -> QuerySet[Message]:
        """Возвращает только сообщения текущего пользователя."""
        user = cast(User, self.request.user)
        return Message.objects.filter(owner=user)


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление сообщения."""

    model = Message
    template_name = "mail_messages/message_confirm_delete.html"
    success_url = reverse_lazy("mail_messages:message_list")

    def get_queryset(self) -> QuerySet[Message]:
        """Возвращает только сообщения текущего пользователя."""
        user = cast(User, self.request.user)
        return Message.objects.filter(owner=user)
