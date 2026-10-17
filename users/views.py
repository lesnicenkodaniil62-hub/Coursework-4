from typing import Any, cast

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, View

from .forms import CustomUserCreationForm
from .mixins import ManagerRequiredMixin
from .models import UserProfile
from .services import get_user_stats


class RegisterView(CreateView):
    """Регистрация нового пользователя."""

    form_class = CustomUserCreationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:verify_email_sent")

    def form_valid(self, form: CustomUserCreationForm) -> HttpResponse:
        # Сохраняем пользователя, но делаем его неактивным до подтверждения email
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        # Генерируем токен и отправляем письмо
        profile: UserProfile = user.profile
        token = profile.generate_verification_token()

        verify_url = self.request.build_absolute_uri(reverse("users:verify_email", kwargs={"token": token}))

        send_mail(
            subject="Подтверждение регистрации в Messenger",
            message=f"Здравствуйте, {user.username}!\n\n"
            f"Для подтверждения вашего email перейдите по ссылке:\n{verify_url}\n\n"
            f"Если вы не регистрировались, просто проигнорируйте это письмо.",
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return super().form_valid(form)


class VerifyEmailView(View):
    """Подтверждение email по токену."""

    def get(self, request: HttpRequest, token: str) -> HttpResponse:
        profile = get_object_or_404(UserProfile, verification_token=token)

        if profile.is_email_verified:
            messages.info(request, "Этот email уже был подтверждён ранее.")
        else:
            profile.is_email_verified = True
            profile.user.is_active = True
            profile.user.save(update_fields=["is_active"])
            profile.save(update_fields=["is_email_verified"])

            # Автоматически входим в систему
            login(request, profile.user)
            messages.success(request, "Email успешно подтверждён! Добро пожаловать.")

        return redirect("main:dashboard")


class CustomLoginView(LoginView):
    """Кастомный вход с проверкой подтверждения email."""

    template_name = "users/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form: Any) -> HttpResponse:
        user = form.get_user()
        if hasattr(user, "profile") and not user.profile.is_email_verified:
            messages.error(
                request=self.request,
                message="Пожалуйста, подтвердите ваш email перед входом.",
            )
            return redirect("users:login")
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    """Кастомный выход из системы."""

    next_page = "users:login"


# Встроенные представления Django для сброса пароля
class CustomPasswordResetView(PasswordResetView):
    template_name = "users/password_reset.html"
    email_template_name = "users/password_reset_email.txt"
    success_url = reverse_lazy("users:password_reset_done")


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "users/password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "users/password_reset_confirm.html"
    success_url = reverse_lazy("users:password_reset_complete")


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "users/password_reset_complete.html"


class UserStatsView(LoginRequiredMixin, TemplateView):
    """Персональная статистика пользователя."""

    template_name = "users/user_stats.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        user = cast(User, self.request.user)
        context["stats"] = get_user_stats(user)
        return context


class UserManagementView(ManagerRequiredMixin, ListView):
    """Управление пользователями (только для менеджеров)."""

    model = User
    template_name = "users/user_management.html"
    context_object_name = "users"
    paginate_by = 20

    def get_queryset(self) -> QuerySet[User]:
        """Возвращает всех пользователей, кроме суперпользователей."""
        return User.objects.filter(is_superuser=False).order_by("-date_joined")


@login_required
def block_user(request: HttpRequest, pk: int) -> HttpResponse:
    """Блокирует пользователя (только для менеджеров)."""
    user = cast(User, request.user)
    if not user.groups.filter(name="Менеджер").exists():
        raise PermissionDenied("Доступ разрешён только менеджерам.")

    target_user = get_object_or_404(User, pk=pk, is_superuser=False)

    # Менеджер не может заблокировать другого менеджера
    if target_user.groups.filter(name="Менеджер").exists():
        messages.error(request, "Нельзя заблокировать другого менеджера.")
        return redirect("users:user_management")

    # Менеджер не может заблокировать себя
    if target_user == user:
        messages.error(request, "Нельзя заблокировать себя.")
        return redirect("users:user_management")

    target_user.is_active = False
    target_user.save(update_fields=["is_active"])
    messages.success(request, f"Пользователь {target_user.username} заблокирован.")
    return redirect("users:user_management")


@login_required
def unblock_user(request: HttpRequest, pk: int) -> HttpResponse:
    """Разблокирует пользователя (только для менеджеров)."""
    user = cast(User, request.user)
    if not user.groups.filter(name="Менеджер").exists():
        raise PermissionDenied("Доступ разрешён только менеджерам.")

    target_user = get_object_or_404(User, pk=pk, is_superuser=False)
    target_user.is_active = True
    target_user.save(update_fields=["is_active"])
    messages.success(request, f"Пользователь {target_user.username} разблокирован.")
    return redirect("users:user_management")
