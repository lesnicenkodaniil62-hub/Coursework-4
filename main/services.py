from dataclasses import dataclass
from typing import Final

from django.core.cache import cache
from django.utils import timezone

from clients.models import Client
from mailings.models import Mailing

DASHBOARD_CACHE_KEY: Final[str] = "messenger:dashboard:v1"
DASHBOARD_TTL: Final[int] = 300


@dataclass(frozen=True)
class DashboardStats:
    total_mailings: int
    active_mailings: int
    total_clients: int


def get_dashboard_stats() -> DashboardStats:
    cached = cache.get(DASHBOARD_CACHE_KEY)
    if isinstance(cached, DashboardStats):
        return cached

    now = timezone.now()

    total_mailings: int = Mailing.objects.count()

    active_mailings: int = Mailing.objects.filter(
        status=Mailing.STATUS_RUNNING,
        start_time__lte=now,
        end_time__gte=now,
    ).count()

    total_clients: int = Client.objects.count()

    stats = DashboardStats(
        total_mailings=total_mailings,
        active_mailings=active_mailings,
        total_clients=total_clients,
    )

    cache.set(DASHBOARD_CACHE_KEY, stats, DASHBOARD_TTL)
    return stats


def invalidate_dashboard_cache() -> None:
    cache.delete(DASHBOARD_CACHE_KEY)
