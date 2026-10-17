import secrets

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Расширенный профиль пользователя для подтверждения email."""

    user: models.OneToOneField = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
    )
    is_email_verified: models.BooleanField = models.BooleanField(
        default=False,
        verbose_name="Email подтверждён",
    )
    verification_token: models.CharField = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Токен подтверждения",
    )

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self) -> str:
        return f"Профиль {self.user.username}"

    def generate_verification_token(self) -> str:
        """Генерирует и сохраняет новый токен."""
        self.verification_token = secrets.token_urlsafe(32)
        self.save(update_fields=["verification_token"])
        return self.verification_token


@receiver(post_save, sender=User)
def create_user_profile(
    sender: type[User],
    instance: User,
    created: bool,
    **kwargs,
) -> None:
    """Автоматически создаёт профиль при создании пользователя."""
    if created:
        UserProfile.objects.create(user=instance)
