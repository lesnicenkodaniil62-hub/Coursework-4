from typing import TYPE_CHECKING, Any, cast

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet

if TYPE_CHECKING:
    from django.http import HttpRequest


class ManagerRequiredMixin(UserPassesTestMixin):
    """Миксин для проверки роли менеджера."""

    request: "HttpRequest"

    def test_func(self) -> bool:
        """Проверяет, что пользователь является менеджером."""
        user = cast(User, self.request.user)
        if not user.is_authenticated:
            return False
        return user.groups.filter(name="Менеджер").exists()

    def handle_no_permission(self) -> Any:
        """Отказывает в доступе, если пользователь не менеджер."""
        raise PermissionDenied("Доступ разрешён только менеджерам.")


class OwnerFilterMixin:
    """Миксин для фильтрации данных по владельцу (для обычных пользователей)."""

    request: "HttpRequest"

    def get_queryset(self) -> QuerySet[Any]:
        """Возвращает все объекты для менеджеров или только свои для обычных пользователей."""
        queryset: QuerySet[Any] = super().get_queryset()  # type: ignore[misc]
        user = cast(User, self.request.user)

        # Если пользователь — менеджер, возвращаем все объекты
        if user.groups.filter(name="Менеджер").exists():
            return queryset

        # Иначе фильтруем по владельцу
        return queryset.filter(owner=user)
