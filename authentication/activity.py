from __future__ import annotations

import threading
from datetime import timedelta
from typing import Any

from django.apps import apps
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.utils import timezone


_state = threading.local()

TRACKED_APP_LABELS = {
    "authentication",
    "data_quality",
    "elements",
    "facilities",
    "health_services",
    "health_workforce",
    "home",
    "indicators",
    "publications",
    "regions",
    "uhc_clock",
}

IGNORED_MODELS = {
    "AhodctUserLogs",
}

IGNORED_FIELD_NAMES = {
    "date_lastupdated",
    "last_login",
    "password",
}


class ActivityLogMiddleware:
    """Expose the authenticated request user to model-signal activity logging."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _state.user = getattr(request, "user", None)
        _state.path = getattr(request, "path", "")
        try:
            return self.get_response(request)
        finally:
            _state.user = None
            _state.path = ""


def register_activity_logging() -> None:
    for model in apps.get_models():
        if not _should_track_model(model):
            continue
        post_save.connect(_record_saved_model, sender=model, dispatch_uid=f"aho_activity_save_{model._meta.label_lower}")
        post_delete.connect(_record_deleted_model, sender=model, dispatch_uid=f"aho_activity_delete_{model._meta.label_lower}")


def _should_track_model(model) -> bool:
    meta = model._meta
    if meta.app_label not in TRACKED_APP_LABELS:
        return False
    if meta.auto_created or not meta.managed or model.__name__ in IGNORED_MODELS:
        return False
    if model.__name__.endswith("Translation"):
        return False
    return True


def _record_saved_model(sender, instance, created: bool, **kwargs) -> None:
    update_fields = kwargs.get("update_fields")
    changed_fields = [field for field in (update_fields or []) if field not in IGNORED_FIELD_NAMES]
    message = "Record updated from application activity log."
    if changed_fields:
        message = f"Changed fields: {', '.join(changed_fields[:8])}."
    _record_activity(
        instance=instance,
        action_flag=ADDITION if created else CHANGE,
        message="Created from application activity log." if created else message,
    )


def _record_deleted_model(sender, instance, **kwargs) -> None:
    _record_activity(
        instance=instance,
        action_flag=DELETION,
        message="Deleted from application activity log.",
    )


def _record_activity(*, instance: Any, action_flag: int, message: str) -> None:
    user = getattr(_state, "user", None)
    if not getattr(user, "is_authenticated", False):
        return
    path = getattr(_state, "path", "") or ""
    if "/admin/" in path or path.rstrip("/").endswith("/admin"):
        return

    content_type = ContentType.objects.get_for_model(instance, for_concrete_model=False)
    object_id = str(getattr(instance, instance._meta.pk.attname, ""))
    object_repr = str(instance)[:200]

    def create_log_if_needed() -> None:
        recent_since = timezone.now() - timedelta(seconds=5)
        exists = LogEntry.objects.filter(
            user_id=user.pk,
            content_type_id=content_type.pk,
            object_id=object_id,
            action_flag=action_flag,
            action_time__gte=recent_since,
        ).exists()
        if exists:
            return
        LogEntry.objects.create(
            user_id=user.pk,
            content_type_id=content_type.pk,
            object_id=object_id,
            object_repr=object_repr,
            action_flag=action_flag,
            change_message=message,
        )

    transaction.on_commit(create_log_if_needed)
