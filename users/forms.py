from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class CustomUserCreationForm(UserCreationForm):
    """Форма регистрации с обязательным email и проверкой его уникальности."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"}),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "Имя пользователя"}),
            "password1": forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Пароль"}),
            "password2": forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Повторите пароль"}),
        }

    def clean_email(self) -> str:
        """Проверяет, что email ещё не занят."""
        email: str | None = self.cleaned_data.get("email")
        if not email:
            raise ValidationError("Email обязателен для заполнения.")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже зарегистрирован.")
        return email
