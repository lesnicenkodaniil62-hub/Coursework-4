from typing import Any

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, View

from .forms import CustomUserCreationForm
from .models import UserProfile


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
            messages.error(request=self.request, message="Пожалуйста, подтвердите ваш email перед входом.")
            return redirect("users:login")
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    """Кастомный выход из системы."""

    next_page = "users:login"


# Встроенные представления Django для сброса пароля
class CustomPasswordResetView(PasswordResetView):
    template_name = "users/password_reset.html"
    email_template_name = "users/password_reset_email.txt"  # Можно создать отдельно, или использовать дефолтный
    success_url = reverse_lazy("users:password_reset_done")


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "users/password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "users/password_reset_confirm.html"
    success_url = reverse_lazy("users:password_reset_complete")


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "users/password_reset_complete.html"
