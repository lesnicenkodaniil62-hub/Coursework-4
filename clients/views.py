from typing import Any, cast

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from users.mixins import OwnerFilterMixin, OwnerOnlyMixin

from .forms import ClientForm
from .models import Client


class ClientListView(LoginRequiredMixin, OwnerFilterMixin, ListView):
    """Список всех клиентов текущего пользователя."""

    model = Client
    template_name = "clients/client_list.html"
    context_object_name = "clients"
    paginate_by = 10


class ClientDetailView(LoginRequiredMixin, OwnerFilterMixin, DetailView):
    """Детальная информация о клиенте."""

    model = Client
    template_name = "clients/client_detail.html"
    context_object_name = "client"


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


class ClientUpdateView(LoginRequiredMixin, OwnerOnlyMixin, UpdateView):
    """Редактирование клиента."""

    model = Client
    form_class = ClientForm
    template_name = "clients/client_form.html"
    success_url = reverse_lazy("clients:client_list")


class ClientDeleteView(LoginRequiredMixin, OwnerOnlyMixin, DeleteView):  # type: ignore[misc]
    """Удаление клиента."""

    model = Client
    template_name = "clients/client_confirm_delete.html"
    success_url = reverse_lazy("clients:client_list")
