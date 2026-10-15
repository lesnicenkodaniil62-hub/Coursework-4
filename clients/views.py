from typing import Any, cast

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import ClientForm
from .models import Client


class ClientListView(LoginRequiredMixin, ListView):
    """Список всех клиентов текущего пользователя."""

    model = Client
    template_name = "clients/client_list.html"
    context_object_name = "clients"
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Client]:
        """Возвращает только клиентов текущего пользователя."""
        user = cast(User, self.request.user)
        return Client.objects.filter(owner=user)


class ClientDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о клиенте."""

    model = Client
    template_name = "clients/client_detail.html"
    context_object_name = "client"

    def get_queryset(self) -> QuerySet[Client]:
        """Возвращает только клиентов текущего пользователя."""
        user = cast(User, self.request.user)
        return Client.objects.filter(owner=user)


class ClientCreateView(LoginRequiredMixin, CreateView):
    """Создание нового клиента."""

    model = Client
    form_class = ClientForm
    template_name = "clients/client_form.html"
    success_url = reverse_lazy("clients:client_list")

    def form_valid(self, form: ClientForm) -> Any:
        """Устанавливает владельца перед сохранением."""
        user = cast(User, self.request.user)
        form.instance.owner = user
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование клиента."""

    model = Client
    form_class = ClientForm
    template_name = "clients/client_form.html"
    success_url = reverse_lazy("clients:client_list")

    def get_queryset(self) -> QuerySet[Client]:
        """Возвращает только клиентов текущего пользователя."""
        user = cast(User, self.request.user)
        return Client.objects.filter(owner=user)


class ClientDeleteView(LoginRequiredMixin, DeleteView):  # type: ignore[misc]
    """Удаление клиента."""

    model = Client
    template_name = "clients/client_confirm_delete.html"
    success_url = reverse_lazy("clients:client_list")

    def get_queryset(self) -> QuerySet[Client]:
        user = cast(User, self.request.user)
        return Client.objects.filter(owner=user)
