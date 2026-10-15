from typing import Any, cast

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from clients.models import Client
from mail_messages.models import Message

from .models import Mailing


class MailingForm(forms.ModelForm):
    """Форма для создания и редактирования рассылки."""

    message = forms.ModelChoiceField(
        queryset=Message.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Сообщение",
    )
    recipients = forms.ModelMultipleChoiceField(
        queryset=Client.objects.none(),
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": 5}),
        label="Получатели",
    )

    class Meta:
        model = Mailing
        fields = ["start_time", "end_time", "message", "recipients"]
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Фильтруем сообщения и получателей по владельцу."""
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user:
            message_field = cast(forms.ModelChoiceField, self.fields["message"])
            recipients_field = cast(forms.ModelMultipleChoiceField, self.fields["recipients"])
            message_field.queryset = Message.objects.filter(owner=self.user)
            recipients_field.queryset = Client.objects.filter(owner=self.user)

    def clean_start_time(self) -> Any:
        """Проверяем, что start_time не в прошлом."""
        start_time = self.cleaned_data.get("start_time")
        if start_time and start_time < timezone.now():
            raise ValidationError("Дата начала не может быть в прошлом.")
        return start_time

    def clean(self) -> dict[str, Any]:
        """Проверяем, что start_time < end_time."""
        cleaned_data = super().clean()
        if cleaned_data is None:
            return {}

        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time and start_time >= end_time:
            raise ValidationError("Дата окончания должна быть позже даты начала.")

        return cleaned_data
