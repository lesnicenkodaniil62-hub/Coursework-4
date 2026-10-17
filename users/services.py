from dataclasses import dataclass
from typing import Final

from django.contrib.auth.models import User

from mailings.models import Mailing, MailingAttempt

USER_STATS_CACHE_KEY_PREFIX: Final[str] = "messenger:user_stats:v1:"


@dataclass(frozen=True)
class UserStats:
    """Персональная статистика пользователя."""

    total_mailings: int
    total_attempts: int
    successful_attempts: int
    failed_attempts: int
    total_messages_sent: int


def get_user_stats(user: User) -> UserStats:
    """Рассчитывает персональную статистику пользователя."""
    user_mailings = Mailing.objects.filter(owner=user)

    total_mailings: int = user_mailings.count()

    attempts = MailingAttempt.objects.filter(mailing__owner=user)
    total_attempts: int = attempts.count()

    successful_attempts: int = attempts.filter(status=MailingAttempt.STATUS_SUCCESS).count()

    failed_attempts: int = attempts.filter(status=MailingAttempt.STATUS_FAILED).count()

    # Количество отправленных сообщений = количество успешных попыток
    # (каждая попытка = одно письмо одному получателю)
    total_messages_sent: int = successful_attempts

    return UserStats(
        total_mailings=total_mailings,
        total_attempts=total_attempts,
        successful_attempts=successful_attempts,
        failed_attempts=failed_attempts,
        total_messages_sent=total_messages_sent,
    )
