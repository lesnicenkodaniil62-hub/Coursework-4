from typing import Any

from django.db.models import Model
from django.db.models.signals import post_delete, post_save

from clients.models import Client
from mailings.models import Mailing

from .services import invalidate_dashboard_cache


def invalidate_dashboard(
    sender: type[Model],
    instance: Model,
    **kwargs: Any,
) -> None:
    invalidate_dashboard_cache()


def register_dashboard_signals() -> None:
    post_save.connect(
        invalidate_dashboard,
        sender=Client,
        dispatch_uid="main_client_post_save",
    )
    post_delete.connect(
        invalidate_dashboard,
        sender=Client,
        dispatch_uid="main_client_post_delete",
    )
    post_save.connect(
        invalidate_dashboard,
        sender=Mailing,
        dispatch_uid="main_mailing_post_save",
    )
    post_delete.connect(
        invalidate_dashboard,
        sender=Mailing,
        dispatch_uid="main_mailing_post_delete",
    )
