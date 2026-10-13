from django import forms
from django.core.exceptions import ValidationError

from .models import Client


class ClientForm(forms.ModelForm):
    """Форма для создания и редактирования получателя рассылки."""

    class Meta:
        model = Client
        fields = ["email", "full_name", "comment"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def clean_email(self) -> str:
        """Валидация уникальности email."""
        email: str = self.cleaned_data["email"]
        if self.instance.pk:
            # При редактировании проверяем, не занят ли email другим клиентом
            if Client.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise ValidationError("Клиент с таким email уже существует.")
        else:
            # При создании проверяем, не занят ли email
            if Client.objects.filter(email=email).exists():
                raise ValidationError("Клиент с таким email уже существует.")
        return email
