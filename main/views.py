from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponseBase
from django.utils.cache import patch_cache_control
from django.views.generic import TemplateView

from .services import get_dashboard_stats


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "main/dashboard.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["stats"] = get_dashboard_stats()
        return context

    def dispatch(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponseBase:
        response: HttpResponseBase = super().dispatch(request, *args, **kwargs)
        patch_cache_control(response, private=True, max_age=60)
        return response
