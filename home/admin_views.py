from __future__ import annotations

from typing import Any
from urllib.parse import urlencode, urlparse

from django.contrib import admin
from django.contrib.admin.models import CHANGE, DELETION, LogEntry
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import DatabaseError, connection
from django.db.models import Q
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils import translation
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST
from rest_framework.authtoken.models import Token


GLOBAL_DIRECT_SEARCHES = [
    {
        "model": "regions.StgLocationCodes",
        "fields": ("location__translations__name", "country_code"),
        "direct_queryset_for_superuser": True,
    },
    {
        "model": "indicators.StgIndicator",
        "fields": (
            "translations__name",
            "translations__shortname",
            "translations__definition",
            "afrocode",
            "gen_code",
        ),
    },
    {
        "model": "home.StgDatasource",
        "fields": ("translations__name", "translations__shortname", "translations__description", "code"),
    },
    {
        "model": "home.StgCategoryoption",
        "fields": ("translations__name", "translations__shortname", "translations__description", "code"),
    },
    {
        "model": "home.StgMeasuremethod",
        "fields": ("translations__name", "translations__description", "code"),
    },
    {
        "model": "publications.StgKnowledgeProduct",
        "fields": (
            "translations__title",
            "translations__description",
            "translations__author",
            "location__translations__name",
            "code",
            "comment",
        ),
    },
    {
        "model": "elements.StgDataElement",
        "fields": ("translations__name", "translations__shortname", "translations__description", "code"),
    },
    {
        "model": "health_services.HealthServicesIndicators",
        "fields": ("translations__name", "translations__shortname", "afrocode", "gen_code"),
    },
    {
        "model": "facilities.StgHealthFacility",
        "fields": ("name", "shortname", "code", "status", "location__translations__name"),
    },
    {
        "model": "authentication.CustomUser",
        "fields": ("email", "username", "first_name", "last_name"),
    },
]

GLOBAL_TABLE_SEARCH_LINKS = [
    ("indicators.FactDataIndicator", "indicator_values"),
    ("indicators.aho_factsindicator_archive", "indicator_archives"),
    ("elements.FactDataElement", "data_element_values"),
    ("health_services.HealthServices_DataIndicators", "health_service_values"),
    ("health_workforce.StgHealthWorkforceFacts", "workforce_values"),
    ("data_quality.Facts_DataFrame", "data_quality_facts"),
]

GLOBAL_TABLE_LABELS = {
    "en": {
        "indicator_values": 'Search "%(query)s" in indicator values',
        "indicator_archives": 'Search "%(query)s" in indicator archives',
        "data_element_values": 'Search "%(query)s" in data element values',
        "health_service_values": 'Search "%(query)s" in health service values',
        "workforce_values": 'Search "%(query)s" in health workforce values',
        "data_quality_facts": 'Search "%(query)s" in data quality facts',
        "search_scope": "Global search",
    },
    "fr": {
        "indicator_values": 'Rechercher "%(query)s" dans les valeurs des indicateurs',
        "indicator_archives": 'Rechercher "%(query)s" dans les archives des indicateurs',
        "data_element_values": 'Rechercher "%(query)s" dans les valeurs des elements de donnees',
        "health_service_values": 'Rechercher "%(query)s" dans les valeurs des services de sante',
        "workforce_values": 'Rechercher "%(query)s" dans les valeurs du personnel de sante',
        "data_quality_facts": 'Rechercher "%(query)s" dans les donnees de qualite',
        "search_scope": "Recherche globale",
    },
    "pt": {
        "indicator_values": 'Pesquisar "%(query)s" nos valores dos indicadores',
        "indicator_archives": 'Pesquisar "%(query)s" nos arquivos dos indicadores',
        "data_element_values": 'Pesquisar "%(query)s" nos valores dos elementos de dados',
        "health_service_values": 'Pesquisar "%(query)s" nos valores dos servicos de saude',
        "workforce_values": 'Pesquisar "%(query)s" nos valores da forca de trabalho',
        "data_quality_facts": 'Pesquisar "%(query)s" nos dados de qualidade',
        "search_scope": "Pesquisa global",
    },
}


def _dictfetchall(cursor) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _query_rows(sql: str) -> list[dict[str, Any]]:
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            return _dictfetchall(cursor)
    except DatabaseError:
        return []


def _table_context(request, *, title: str, subtitle: str, headers, rows, metrics=None):
    context = admin.site.each_context(request)
    context.update(
        {
            "title": title,
            "subtitle": subtitle,
            "headers": headers,
            "rows": rows,
            "metrics": metrics or [],
        }
    )
    return context


def _display(value: Any) -> str:
    try:
        text = str(value)
    except Exception:
        text = ""
    return text.strip()


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _host_from_url(value: Any) -> str:
    text = _display(value)
    if not text:
        return ""
    parsed = urlparse(text)
    if parsed.netloc:
        return parsed.netloc
    return text.split("/", 1)[0] if "/" in text else text


def _log_admin_action(request, obj: Any, action_flag: int, message: str) -> None:
    if not getattr(request.user, "is_authenticated", False):
        return
    content_type = ContentType.objects.get_for_model(obj, for_concrete_model=False)
    LogEntry.objects.create(
        user_id=request.user.pk,
        content_type_id=content_type.pk,
        object_id=str(getattr(obj, obj._meta.pk.attname, "")),
        object_repr=str(obj)[:200],
        action_flag=action_flag,
        change_message=message,
    )


def _admin_change_url(model, obj) -> str | None:
    try:
        return reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_change", args=[obj.pk])
    except NoReverseMatch:
        return None


def _admin_changelist_url(model, query: str = "") -> str | None:
    try:
        url = reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist")
    except NoReverseMatch:
        return None
    if query:
        return f"{url}?{urlencode({'q': query})}"
    return url


def _fallback_search_fields(model) -> list[str]:
    field_types = {"CharField", "TextField", "EmailField", "SlugField", "URLField"}
    fields: list[str] = []
    for field in model._meta.get_fields():
        if getattr(field, "is_relation", False):
            continue
        if getattr(field, "get_internal_type", lambda: "")() in field_types:
            fields.append(field.name)
        if len(fields) >= 4:
            break
    return fields


def _search_text(key: str, query: str = "") -> str:
    lang = (translation.get_language() or "en").split("-", 1)[0]
    labels = GLOBAL_TABLE_LABELS.get(lang, GLOBAL_TABLE_LABELS["en"])
    template = labels.get(key, GLOBAL_TABLE_LABELS["en"].get(key, key))
    return template % {"query": query}


def _model_from_path(model_path: str):
    try:
        app_label, model_name = model_path.split(".", 1)
        return apps.get_model(app_label, model_name)
    except LookupError:
        return None


def _has_admin_view_permission(request, model) -> bool:
    model_admin = admin.site._registry.get(model)
    if model_admin is None:
        return False
    return model_admin.has_view_permission(request)


def _build_search_filter(fields: tuple[str, ...], query: str) -> Q:
    search_filter = Q()
    for field in fields:
        search_filter |= Q(**{f"{field}__icontains": query})
    return search_filter


def _append_object_results(
    request,
    results: list[dict[str, str]],
    seen: set[tuple[str, str, str]],
    *,
    model_path: str,
    fields: tuple[str, ...],
    query: str,
    limit: int = 3,
    direct_queryset_for_superuser: bool = False,
) -> None:
    model = _model_from_path(model_path)
    if model is None:
        return
    model_admin = admin.site._registry.get(model)
    if model_admin is None or not model_admin.has_view_permission(request):
        return

    try:
        if direct_queryset_for_superuser and getattr(request.user, "is_superuser", False):
            queryset = model._default_manager.all()
        else:
            queryset = model_admin.get_queryset(request)
        queryset = queryset.filter(_build_search_filter(fields, query))
        if not direct_queryset_for_superuser:
            queryset = queryset.distinct()
        lookup_limit = limit * 4 if direct_queryset_for_superuser else limit
        added = 0
        for obj in queryset[:lookup_limit]:
            key = (model._meta.app_label, model._meta.model_name, str(obj.pk))
            if key in seen:
                continue
            seen.add(key)
            try:
                label = str(obj).strip()
            except Exception:
                label = f"{model._meta.verbose_name.title()} #{obj.pk}"
            label = label or f"{model._meta.verbose_name.title()} #{obj.pk}"
            if len(label) > 120:
                label = f"{label[:117]}..."
            url = _admin_change_url(model, obj) if model_admin.has_change_permission(request, obj) else None
            url = url or _admin_changelist_url(model, query) or "#"
            results.append(
                {
                    "label": label,
                    "subtitle": f"{model._meta.verbose_name_plural.title()} / {model._meta.app_label}",
                    "url": url,
                }
            )
            added += 1
            if added >= limit:
                break
    except Exception:
        return


def _append_table_search_links(request, results: list[dict[str, str]], query: str) -> None:
    for model_path, label_key in GLOBAL_TABLE_SEARCH_LINKS:
        model = _model_from_path(model_path)
        if model is None or not _has_admin_view_permission(request, model):
            continue
        url = _admin_changelist_url(model, query)
        if not url:
            continue
        results.append(
            {
                "label": _search_text(label_key, query),
                "subtitle": _search_text("search_scope"),
                "url": url,
            }
        )


def _append_location_results(
    request,
    results: list[dict[str, str]],
    seen: set[tuple[str, str, str]],
    query: str,
    limit: int = 5,
) -> None:
    model = _model_from_path("regions.StgLocation")
    if model is None or not _has_admin_view_permission(request, model):
        return

    language = getattr(request, "LANGUAGE_CODE", None) or (translation.get_language() or "en").split("-", 1)[0]
    lookup = f"%{query}%"
    sql = """
        SELECT l.location_id, t.name, l.iso_alpha, l.code
        FROM stg_location l
        INNER JOIN stg_location_translation t ON t.master_id = l.location_id
        WHERE t.language_code = %s
            AND (
                t.name LIKE %s
                OR l.iso_alpha LIKE %s
                OR l.iso_number LIKE %s
                OR l.code LIKE %s
            )
        LIMIT %s
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, [language, lookup, lookup, lookup, lookup, limit])
            rows = cursor.fetchall()
    except DatabaseError:
        return

    model_admin = admin.site._registry.get(model)
    for location_id, name, iso_alpha, code in rows:
        key = ("regions", "stglocation", str(location_id))
        if key in seen:
            continue
        seen.add(key)
        try:
            url = reverse("admin:regions_stglocation_change", args=[location_id])
        except NoReverseMatch:
            url = _admin_changelist_url(model, query) or "#"
        if model_admin and not model_admin.has_change_permission(request):
            url = _admin_changelist_url(model, query) or url
        label = str(name or iso_alpha or code or f"Location #{location_id}").strip()
        results.append(
            {
                "label": label,
                "subtitle": f"{model._meta.verbose_name_plural.title()} / {model._meta.app_label}",
                "url": url,
            }
        )


@staff_member_required
@require_GET
def global_search(request):
    query = (request.GET.get("q") or "").strip()
    if len(query) < 2:
        return JsonResponse({"results": []})
    if not getattr(request, "LANGUAGE_CODE", None):
        request.LANGUAGE_CODE = (translation.get_language() or "en").split("-", 1)[0]

    results: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    _append_location_results(request, results, seen, query)

    for search_config in GLOBAL_DIRECT_SEARCHES:
        if len(results) >= 20:
            break
        _append_object_results(
            request,
            results,
            seen,
            model_path=search_config["model"],
            fields=search_config["fields"],
            query=query,
            direct_queryset_for_superuser=search_config.get("direct_queryset_for_superuser", False),
        )

    _append_table_search_links(request, results, query)

    return JsonResponse({"results": results[:20]})


@staff_member_required
@require_POST
def row_action(request):
    app_label = request.POST.get("app_label")
    model_name = request.POST.get("model_name")
    object_id = request.POST.get("object_id")
    operation = request.POST.get("operation")
    next_url = request.POST.get("next") or reverse("admin:index")

    if not all([app_label, model_name, object_id, operation]):
        return HttpResponseBadRequest(_("Missing row action parameters."))

    try:
        model = apps.get_model(app_label, model_name)
    except LookupError:
        return HttpResponseBadRequest(_("Unknown model."))

    model_admin = admin.site._registry.get(model)
    if model_admin is None:
        return HttpResponseBadRequest(_("Model is not registered in admin."))

    try:
        obj = model_admin.get_queryset(request).get(pk=object_id)
    except Exception:
        return HttpResponseBadRequest(_("Record was not found."))

    if operation == "delete":
        if not model_admin.has_delete_permission(request, obj):
            return HttpResponseBadRequest(_("You do not have permission to delete this record."))
        label = str(obj)
        _log_admin_action(request, obj, DELETION, _("Deleted from table action."))
        obj.delete()
        messages.success(request, _("Deleted: %(label)s") % {"label": label})
        return redirect(next_url)

    if operation in {"approved", "pending", "rejected"}:
        if not model_admin.has_change_permission(request, obj):
            return HttpResponseBadRequest(_("You do not have permission to update this record."))
        status_field = None
        for candidate in ("comment", "status"):
            try:
                model._meta.get_field(candidate)
                status_field = candidate
                break
            except Exception:
                continue
        if status_field is None:
            return HttpResponseBadRequest(_("This record has no approval status field."))
        setattr(obj, status_field, operation)
        obj.save(update_fields=[status_field])
        _log_admin_action(request, obj, CHANGE, _("Status updated to %(status)s.") % {"status": operation})
        messages.success(request, _("Status updated to %(status)s.") % {"status": operation})
        return redirect(next_url)

    return HttpResponseBadRequest(_("Unknown row action."))


def _wizard_status(events: str, failed_rows: int, imported_rows: int) -> str:
    if failed_rows:
        return _("Completed with errors")
    if "import_complete" in events:
        return _("Completed")
    if imported_rows:
        return _("Imported")
    if "do_import" in events or "auto_import" in events:
        return _("Processing")
    return _("Prepared")


def _indicator_wizard_rows() -> list[dict[str, Any]]:
    rows = _query_rows(
        """
        SELECT
            run.id,
            run.serializer,
            run.loader,
            run.record_count,
            COALESCE(f.name, u.name) AS name,
            COALESCE(f.file, u.url) AS source,
            CASE WHEN u.id IS NOT NULL THEN 'URL' ELSE 'File' END AS source_type,
            COALESCE(hf.location_id, hu.location_id) AS location_id,
            COALESCE(hf.user_id, hu.user_id, run.user_id) AS owner_id,
            COUNT(r.id) AS imported_rows,
            SUM(CASE WHEN r.success = 0 THEN 1 ELSE 0 END) AS failed_rows,
            GROUP_CONCAT(DISTINCT l.event ORDER BY l.date SEPARATOR ', ') AS events,
            COALESCE(MAX(l.date), f.date, u.date) AS activity_at
        FROM data_wizard_run run
        LEFT JOIN data_wizard_filesource f
            ON run.content_type_id = 19 AND f.id = run.object_id
        LEFT JOIN home_filesource hf
            ON hf.filesource_ptr_id = f.id
        LEFT JOIN data_wizard_urlsource u
            ON run.content_type_id = 20 AND u.id = run.object_id
        LEFT JOIN home_urlsource hu
            ON hu.urlsource_ptr_id = u.id
        LEFT JOIN data_wizard_record r
            ON r.run_id = run.id
        LEFT JOIN django_content_type rct
            ON rct.id = r.content_type_id
        LEFT JOIN data_wizard_runlog l
            ON l.run_id = run.id
        WHERE run.serializer LIKE '%FactIndicator%'
            OR (rct.app_label = 'indicators' AND rct.model = 'factdataindicator')
        GROUP BY
            run.id,
            run.serializer,
            run.loader,
            run.record_count,
            f.name,
            f.file,
            f.date,
            u.name,
            u.url,
            u.date,
            u.id,
            hf.location_id,
            hu.location_id,
            hf.user_id,
            hu.user_id,
            run.user_id
        ORDER BY activity_at DESC, run.id DESC
        LIMIT 150
        """
    )

    formatted_rows = []
    for row in rows:
        events = row.get("events") or ""
        imported_rows = _safe_int(row.get("imported_rows"))
        failed_rows = _safe_int(row.get("failed_rows"))
        formatted_rows.append(
            {
                "id": row.get("id"),
                "name": row.get("name") or _("Indicator source"),
                "source": row.get("source") or "",
                "source_type": _(row.get("source_type") or "File"),
                "records": _safe_int(row.get("record_count")) or imported_rows,
                "imported": imported_rows,
                "failed": failed_rows,
                "location": row.get("location_id") or "",
                "user": row.get("owner_id") or "",
                "events": events,
                "status": _wizard_status(events, failed_rows, imported_rows),
                "activity_at": row.get("activity_at") or "",
            }
        )
    return formatted_rows


@staff_member_required
def indicator_imports(request):
    rows = _indicator_wizard_rows()
    headers = [
        {"key": "id", "label": _("ID")},
        {"key": "name", "label": _("Name")},
        {"key": "source", "label": _("Source")},
        {"key": "source_type", "label": _("Type")},
        {"key": "records", "label": _("Records")},
        {"key": "imported", "label": _("Imported rows")},
        {"key": "failed", "label": _("Failed rows")},
        {"key": "location", "label": _("Location")},
        {"key": "user", "label": _("User")},
        {"key": "status", "label": _("Status")},
        {"key": "activity_at", "label": _("Last activity")},
    ]
    context = _table_context(
        request,
        title=_("Indicator import files"),
        subtitle=_("Excel and CSV files used for indicator data imports."),
        headers=headers,
        rows=rows,
        metrics=[
            {"label": _("Import runs"), "value": len(rows)},
            {"label": _("Imported rows"), "value": sum(_safe_int(row["imported"]) for row in rows)},
            {"label": _("Failed rows"), "value": sum(_safe_int(row["failed"]) for row in rows)},
        ],
    )
    return render(request, "admin/aho_table_page.html", context)


@staff_member_required
def indicator_exports(request):
    export_events = _query_rows(
        """
        SELECT
            l.id,
            run.id AS run_id,
            COALESCE(f.name, u.name) AS name,
            COALESCE(f.file, u.url) AS source,
            CASE WHEN u.id IS NOT NULL THEN 'URL' ELSE 'File' END AS source_type,
            COALESCE(hf.location_id, hu.location_id) AS location_id,
            COALESCE(hf.user_id, hu.user_id, run.user_id) AS owner_id,
            run.record_count,
            l.event,
            l.date AS activity_at
        FROM data_wizard_runlog l
        INNER JOIN data_wizard_run run ON run.id = l.run_id
        LEFT JOIN data_wizard_filesource f
            ON run.content_type_id = 19 AND f.id = run.object_id
        LEFT JOIN home_filesource hf
            ON hf.filesource_ptr_id = f.id
        LEFT JOIN data_wizard_urlsource u
            ON run.content_type_id = 20 AND u.id = run.object_id
        LEFT JOIN home_urlsource hu
            ON hu.urlsource_ptr_id = u.id
        WHERE l.event LIKE '%export%'
            AND run.serializer LIKE '%FactIndicator%'
        ORDER BY l.date DESC, l.id DESC
        LIMIT 150
        """
    )

    if export_events:
        rows = [
            {
                "id": row.get("id"),
                "name": row.get("name") or _("Indicator export"),
                "source": row.get("source") or "",
                "source_type": _(row.get("source_type") or "File"),
                "records": _safe_int(row.get("record_count")),
                "location": row.get("location_id") or "",
                "user": row.get("owner_id") or "",
                "event": row.get("event") or _("Export"),
                "status": _("Completed"),
                "activity_at": row.get("activity_at") or "",
            }
            for row in export_events
        ]
    else:
        rows = []
        for row in _indicator_wizard_rows():
            rows.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "source": row["source"],
                    "source_type": row["source_type"],
                    "records": row["records"],
                    "location": row["location"],
                    "user": row["user"],
                    "event": _("Source file used for indicators"),
                    "status": _("Available"),
                    "activity_at": row["activity_at"],
                }
            )

    headers = [
        {"key": "id", "label": _("ID")},
        {"key": "name", "label": _("Name")},
        {"key": "source", "label": _("Source")},
        {"key": "source_type", "label": _("Type")},
        {"key": "records", "label": _("Records")},
        {"key": "location", "label": _("Location")},
        {"key": "user", "label": _("User")},
        {"key": "event", "label": _("Event")},
        {"key": "status", "label": _("Status")},
        {"key": "activity_at", "label": _("Last activity")},
    ]
    context = _table_context(
        request,
        title=_("Indicator export files"),
        subtitle=_("Export history is shown when available; otherwise the table lists indicator source files available for export."),
        headers=headers,
        rows=rows,
        metrics=[
            {"label": _("Files"), "value": len(rows)},
            {"label": _("Records"), "value": sum(_safe_int(row["records"]) for row in rows)},
        ],
    )
    return render(request, "admin/aho_table_page.html", context)


def _quality_issue_url(model_path: str, object_id: Any) -> str:
    model = _model_from_path(model_path)
    if model is None:
        return "#"
    try:
        return reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_change", args=[object_id])
    except NoReverseMatch:
        return "#"


def _quality_rule_label(rule: str) -> str:
    labels = {
        "negative_value": _("Negative value"),
        "percentage_above_100": _("Percentage above 100"),
        "percentage_looks_like_index": _("Percentage entered as index"),
        "zero_denominator": _("Zero denominator"),
        "missing_values": _("Missing values"),
        "multiple_measures": _("Multiple measures"),
        "invalid_category": _("Invalid category option"),
        "invalid_source": _("Invalid data source"),
        "invalid_measure": _("Invalid measure type"),
        "invalid_period": _("Invalid period"),
        "external_consistency": _("External consistency"),
        "internal_consistency": _("Internal consistency"),
        "value_type": _("Value type consistency"),
    }
    return labels.get(rule, rule.replace("_", " ").title())


def _indicator_text(indicator: Any) -> str:
    try:
        return str(indicator or "")
    except Exception:
        return ""


def _looks_like_percentage(text: str) -> bool:
    normalized = text.lower()
    return "%" in normalized or any(
        term in normalized
        for term in (
            "percentage",
            "percent",
            "proportion",
            "coverage",
            "couverture",
            "pourcentage",
            "proporcao",
            "percentagem",
        )
    )


def _quality_issue(
    *,
    fact_id: Any,
    edit_url: str,
    severity: str,
    rule: str,
    indicator: Any,
    location: Any,
    period: Any,
    value: Any,
    message: str,
) -> dict[str, Any]:
    searchable = " ".join(
        str(part or "")
        for part in (fact_id, severity, rule, indicator, location, period, value, message)
    ).lower()
    return {
        "fact_id": fact_id,
        "edit_url": edit_url,
        "severity": severity,
        "severity_label": _("Error") if severity == "error" else _("Warning"),
        "rule": rule,
        "rule_label": _quality_rule_label(rule),
        "indicator": _indicator_text(indicator),
        "location": _indicator_text(location),
        "period": period or "",
        "value": value if value is not None else "",
        "message": message,
        "search_text": searchable,
    }


def _scan_indicator_quality_issues(request, limit: int = 250) -> tuple[list[dict[str, Any]], int]:
    model = _model_from_path("indicators.FactDataIndicator")
    if model is None:
        return [], 0

    model_admin = admin.site._registry.get(model)
    try:
        queryset = model_admin.get_queryset(request) if model_admin else model.objects.all()
        records = list(
            queryset.select_related("indicator", "location")
            .order_by("-fact_id")[:limit]
        )
    except Exception:
        return [], 0

    issues: list[dict[str, Any]] = []
    for record in records:
        value = getattr(record, "value_received", None)
        numerator = getattr(record, "numerator_value", None)
        denominator = getattr(record, "denominator_value", None)
        numeric_value = float(value) if value is not None else None
        indicator_text = _indicator_text(getattr(record, "indicator", None))
        edit_url = _quality_issue_url("indicators.FactDataIndicator", getattr(record, "fact_id", ""))

        if numeric_value is not None and numeric_value < 0:
            issues.append(
                _quality_issue(
                    fact_id=record.fact_id,
                    edit_url=edit_url,
                    severity="error",
                    rule="negative_value",
                    indicator=record.indicator,
                    location=record.location,
                    period=getattr(record, "period", ""),
                    value=value,
                    message=_("The value cannot be negative."),
                )
            )

        if numeric_value is not None and _looks_like_percentage(indicator_text):
            if numeric_value > 100:
                issues.append(
                    _quality_issue(
                        fact_id=record.fact_id,
                        edit_url=edit_url,
                        severity="error",
                        rule="percentage_above_100",
                        indicator=record.indicator,
                        location=record.location,
                        period=getattr(record, "period", ""),
                        value=value,
                        message=_("The value is above 100 for an indicator expected as percentage."),
                    )
                )
            elif 0 < numeric_value <= 1:
                issues.append(
                    _quality_issue(
                        fact_id=record.fact_id,
                        edit_url=edit_url,
                        severity="warning",
                        rule="percentage_looks_like_index",
                        indicator=record.indicator,
                        location=record.location,
                        period=getattr(record, "period", ""),
                        value=value,
                        message=_("The value looks like an index between 0 and 1, but this indicator is expected as percentage."),
                    )
                )

        if (
            numerator is not None
            and denominator is not None
            and float(denominator) == 0.0
            and float(numerator) > 0
        ):
            issues.append(
                _quality_issue(
                    fact_id=record.fact_id,
                    edit_url=edit_url,
                    severity="error",
                    rule="zero_denominator",
                    indicator=record.indicator,
                    location=record.location,
                    period=getattr(record, "period", ""),
                    value=value,
                    message=_("The denominator is zero while the numerator is positive."),
                )
            )

    return issues, len(records)


def _stored_quality_issues(request, limit: int = 150) -> list[dict[str, Any]]:
    configs = [
        ("data_quality.MissingValuesRemarks", "warning", "missing_values", "remarks"),
        ("data_quality.Mutiple_MeasureTypes", "warning", "multiple_measures", "remarks"),
        ("data_quality.DqaInvalidCategoryoptionRemarks", "error", "invalid_category", "check_category_option"),
        ("data_quality.DqaInvalidDatasourceRemarks", "error", "invalid_source", "check_data_source"),
        ("data_quality.DqaInvalidMeasuretypeRemarks", "error", "invalid_measure", "check_mesure_type"),
        ("data_quality.DqaInvalidPeriodRemarks", "warning", "invalid_period", "check_year"),
        ("data_quality.DqaExternalConsistencyOutliersRemarks", "warning", "external_consistency", "external_consistency"),
        ("data_quality.DqaInternalConsistencyOutliersRemarks", "warning", "internal_consistency", "internal_consistency"),
        ("data_quality.DqaValueTypesConsistencyRemarks", "error", "value_type", "check_value"),
    ]
    issues: list[dict[str, Any]] = []
    for model_path, severity, rule, message_field in configs:
        model = _model_from_path(model_path)
        if model is None:
            continue
        model_admin = admin.site._registry.get(model)
        try:
            queryset = model_admin.get_queryset(request) if model_admin else model.objects.all()
            for obj in queryset.order_by("-id")[: max(1, limit // len(configs))]:
                message = getattr(obj, message_field, None) or _quality_rule_label(rule)
                issues.append(
                    _quality_issue(
                        fact_id=getattr(obj, "id", ""),
                        edit_url=_quality_issue_url(model_path, getattr(obj, "id", "")),
                        severity=severity,
                        rule=rule,
                        indicator=getattr(obj, "indicator_name", ""),
                        location=getattr(obj, "location", ""),
                        period=getattr(obj, "period", ""),
                        value=getattr(obj, "value", ""),
                        message=str(message),
                    )
                )
        except Exception:
            continue
    return issues


@staff_member_required
def data_quality_indicator_checks(request):
    scanned_issues, checked_count = _scan_indicator_quality_issues(request)
    stored_issues = _stored_quality_issues(request)
    issues = (scanned_issues + stored_issues)[:100]
    summary_source = scanned_issues + stored_issues
    summary = {
        "errors": sum(1 for issue in summary_source if issue["severity"] == "error"),
        "warnings": sum(1 for issue in summary_source if issue["severity"] == "warning"),
        "checked": checked_count or len(summary_source),
    }
    context = admin.site.each_context(request)
    context.update(
        {
            "title": _("Indicator checks"),
            "issues": issues,
            "summary": summary,
            "total_issues": summary["errors"] + summary["warnings"],
        }
    )
    return render(request, "admin/aho_quality_page.html", context)


def _dqa_fact_rows(request, limit: int = 150) -> list[dict[str, Any]]:
    model = _model_from_path("data_quality.Facts_DataFrame")
    if model is None:
        return []

    model_admin = admin.site._registry.get(model)
    try:
        queryset = model_admin.get_queryset(request) if model_admin else model.objects.all()
        records = queryset.order_by("-end_period", "indicator_name")[:limit]
    except Exception:
        return []

    rows = []
    for record in records:
        rows.append(
            {
                "fact_id": getattr(record, "fact_id", ""),
                "afrocode": getattr(record, "afrocode", ""),
                "indicator": getattr(record, "indicator_name", ""),
                "location": getattr(record, "location", ""),
                "category_option": getattr(record, "categoryoption", ""),
                "data_source": getattr(record, "datasource", ""),
                "measure_type": getattr(record, "measure_type", ""),
                "value": getattr(record, "value", ""),
                "period": getattr(record, "period", ""),
                "source": _("Data quality view"),
            }
        )
    return rows


def _indicator_fact_rows(request, model_path: str, source_label: str, limit: int = 150) -> list[dict[str, Any]]:
    model = _model_from_path(model_path)
    if model is None:
        return []

    model_admin = admin.site._registry.get(model)
    try:
        queryset = model_admin.get_queryset(request) if model_admin else model.objects.all()
        records = (
            queryset.select_related("indicator", "location", "categoryoption", "datasource", "measuremethod")
            .order_by("-date_created", "-date_lastupdated", "-fact_id")[:limit]
        )
    except Exception:
        try:
            records = model.objects.order_by("-fact_id")[:limit]
        except Exception:
            return []

    rows = []
    for record in records:
        indicator = getattr(record, "indicator", None)
        rows.append(
            {
                "fact_id": getattr(record, "fact_id", ""),
                "afrocode": getattr(indicator, "afrocode", ""),
                "indicator": _display(indicator),
                "location": _display(getattr(record, "location", "")),
                "category_option": _display(getattr(record, "categoryoption", "")),
                "data_source": _display(getattr(record, "datasource", "")),
                "measure_type": _display(getattr(record, "measuremethod", "")),
                "value": getattr(record, "value_received", "") or getattr(record, "string_value", ""),
                "period": getattr(record, "period", "") or getattr(record, "end_period", ""),
                "source": source_label,
            }
        )
    return rows


@staff_member_required
def data_quality_facts_dataset(request):
    rows = _dqa_fact_rows(request)
    source_note = _("Data quality view")
    if not rows:
        rows = _indicator_fact_rows(request, "indicators.FactDataIndicator", _("Fact indicator data"))
        source_note = _("Fact indicator data")
    if not rows:
        rows = _indicator_fact_rows(request, "indicators.aho_factsindicator_archive", _("Archive"))
        source_note = _("Archive")

    headers = [
        {"key": "fact_id", "label": _("ID")},
        {"key": "afrocode", "label": _("Code")},
        {"key": "indicator", "label": _("Indicator")},
        {"key": "location", "label": _("Location")},
        {"key": "category_option", "label": _("Category option")},
        {"key": "data_source", "label": _("Source")},
        {"key": "measure_type", "label": _("Measure type")},
        {"key": "value", "label": _("Received value")},
        {"key": "period", "label": _("Period")},
        {"key": "source", "label": _("Dataset source")},
    ]

    context = _table_context(
        request,
        title=_("Facts dataset"),
        subtitle=_("Fact records used for data-quality checks. If the quality view has no records, the page uses indicator facts, then archives."),
        headers=headers,
        rows=rows,
        metrics=[
            {"label": _("Records"), "value": len(rows)},
            {"label": _("Indicators"), "value": len({row.get("afrocode") or row.get("indicator") for row in rows})},
            {"label": _("Current source"), "value": source_note},
        ],
    )
    return render(request, "admin/aho_table_page.html", context)


@staff_member_required
def data_integration_connections(request):
    file_rows = _query_rows(
        """
        SELECT
            f.id,
            f.name,
            f.file AS source,
            f.date AS created_at,
            hf.url,
            hf.location_id,
            hf.user_id,
            COUNT(DISTINCT run.id) AS runs,
            COUNT(r.id) AS imported_rows,
            SUM(CASE WHEN r.success = 0 THEN 1 ELSE 0 END) AS failed_rows,
            MAX(l.date) AS activity_at
        FROM data_wizard_filesource f
        LEFT JOIN home_filesource hf ON hf.filesource_ptr_id = f.id
        LEFT JOIN django_content_type ct ON ct.app_label = 'sources' AND ct.model = 'filesource'
        LEFT JOIN data_wizard_run run ON run.content_type_id = ct.id AND run.object_id = f.id
        LEFT JOIN data_wizard_record r ON r.run_id = run.id
        LEFT JOIN data_wizard_runlog l ON l.run_id = run.id
        GROUP BY f.id, f.name, f.file, f.date, hf.url, hf.location_id, hf.user_id
        ORDER BY f.date DESC, f.id DESC
        LIMIT 100
        """
    )
    url_rows = _query_rows(
        """
        SELECT
            u.id,
            u.name,
            u.url AS source,
            u.date AS created_at,
            u.url AS url,
            hu.location_id,
            hu.user_id,
            COUNT(DISTINCT run.id) AS runs,
            COUNT(r.id) AS imported_rows,
            SUM(CASE WHEN r.success = 0 THEN 1 ELSE 0 END) AS failed_rows,
            MAX(l.date) AS activity_at
        FROM data_wizard_urlsource u
        LEFT JOIN home_urlsource hu ON hu.urlsource_ptr_id = u.id
        LEFT JOIN django_content_type ct ON ct.app_label = 'sources' AND ct.model = 'urlsource'
        LEFT JOIN data_wizard_run run ON run.content_type_id = ct.id AND run.object_id = u.id
        LEFT JOIN data_wizard_record r ON r.run_id = run.id
        LEFT JOIN data_wizard_runlog l ON l.run_id = run.id
        GROUP BY u.id, u.name, u.url, u.date, hu.location_id, hu.user_id
        ORDER BY u.date DESC, u.id DESC
        LIMIT 100
        """
    )

    rows = []
    for row in file_rows:
        failed_rows = _safe_int(row.get("failed_rows"))
        imported_rows = _safe_int(row.get("imported_rows"))
        source = row.get("url") or row.get("source") or ""
        rows.append(
            {
                "id": row["id"],
                "name": row.get("name") or _("Import file"),
                "provider": _("Django DCT"),
                "integration_method": _("Direct"),
                "status": _("Error") if failed_rows else _("Active"),
                "server_name": _host_from_url(source),
                "api_url": source,
                "sync_frequency": _("Manual"),
                "last_test_status": _("Failed") if failed_rows else _("Validated"),
                "field_mappings_count": imported_rows,
                "last_synced_at": row.get("activity_at") or "",
                "created_at": row.get("created_at") or "",
                "updated_at": row.get("activity_at") or row.get("created_at") or "",
            }
        )

    for row in url_rows:
        failed_rows = _safe_int(row.get("failed_rows"))
        imported_rows = _safe_int(row.get("imported_rows"))
        source = row.get("source") or row.get("url") or ""
        rows.append(
            {
                "id": row["id"],
                "name": row.get("name") or _("Import URL"),
                "provider": _("Custom"),
                "integration_method": _("API"),
                "status": _("Error") if failed_rows else _("Active"),
                "server_name": _host_from_url(source),
                "api_url": source,
                "sync_frequency": _("Manual"),
                "last_test_status": _("Failed") if failed_rows else _("Validated"),
                "field_mappings_count": imported_rows,
                "last_synced_at": row.get("activity_at") or "",
                "created_at": row.get("created_at") or "",
                "updated_at": row.get("activity_at") or row.get("created_at") or "",
            }
        )

    rows.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)

    headers = [
        {"key": "id", "label": _("ID")},
        {"key": "name", "label": _("Name")},
        {"key": "provider", "label": _("Provider")},
        {"key": "integration_method", "label": _("Method")},
        {"key": "status", "label": _("Status")},
        {"key": "server_name", "label": _("Server name")},
        {"key": "api_url", "label": _("API URL")},
        {"key": "sync_frequency", "label": _("Sync frequency")},
        {"key": "last_test_status", "label": _("Last test status")},
        {"key": "field_mappings_count", "label": _("Field mappings")},
        {"key": "last_synced_at", "label": _("Last synced at")},
        {"key": "created_at", "label": _("Created")},
        {"key": "updated_at", "label": _("Modified")},
    ]

    context = _table_context(
        request,
        title=_("Connections"),
        subtitle=_("Data import connections presented with the same structure as the Laravel data integration module."),
        headers=headers,
        rows=rows[:100],
        metrics=[
            {"label": _("Connections"), "value": len(rows)},
            {"label": _("Active"), "value": sum(1 for row in rows if row["status"] == _("Active"))},
            {"label": _("Failed rows"), "value": sum(_safe_int(row["field_mappings_count"]) for row in rows if row["status"] == _("Error"))},
        ],
    )
    return render(request, "admin/aho_table_page.html", context)


@staff_member_required
def data_integration_failed_rows(request):
    rows = _query_rows(
        """
        SELECT
            r.id,
            r.object_id,
            r.row,
            r.fail_reason,
            run.loader,
            run.user_id
        FROM data_wizard_record r
        LEFT JOIN data_wizard_run run ON run.id = r.run_id
        WHERE r.success = 0
        ORDER BY r.id DESC
        LIMIT 100
        """
    )

    headers = [
        {"key": "id", "label": _("ID")},
        {"key": "object_id", "label": _("Object ID")},
        {"key": "row", "label": _("Row")},
        {"key": "fail_reason", "label": _("Failure reason")},
        {"key": "loader", "label": _("Loader")},
        {"key": "user_id", "label": _("User")},
    ]

    context = _table_context(
        request,
        title=_("Failed rows"),
        subtitle=_("Rows rejected by the import workflow."),
        headers=headers,
        rows=rows,
        metrics=[{"label": _("Failed rows"), "value": len(rows)}],
    )
    return render(request, "admin/aho_table_page.html", context)


@staff_member_required
def api_token_status(request):
    plain_token = ""
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            token, created = Token.objects.get_or_create(user=request.user)
            plain_token = token.key
            messages.success(request, _("API token is ready. Copy it now and keep it secure."))
        elif action == "revoke":
            token_id = request.POST.get("token_id")
            queryset = Token.objects.filter(pk=token_id)
            if not request.user.is_superuser:
                queryset = queryset.filter(user=request.user)
            deleted, delete_details = queryset.delete()
            if deleted:
                messages.success(request, _("API token revoked."))
            else:
                messages.warning(request, _("Token was not found or cannot be revoked."))
            return redirect("aho_api_token_status")

    token_queryset = Token.objects.select_related("user").order_by("-created")
    if not request.user.is_superuser:
        token_queryset = token_queryset.filter(user=request.user)
    tokens = token_queryset[:100]

    api_root = request.build_absolute_uri("/api/")
    token_example = plain_token or "YOUR_API_TOKEN"
    endpoints = [
        {"method": "GET", "path": "/api/", "label": _("API documentation"), "scope": _("Read")},
        {"method": "GET", "path": "/api/indicators/", "label": _("List indicators"), "scope": _("Read")},
        {"method": "GET", "path": "/api/indicator_data/", "label": _("List indicator values"), "scope": _("Read")},
        {"method": "POST", "path": "/api/indicator_data/", "label": _("Create indicator value"), "scope": _("Write")},
        {"method": "PUT/PATCH", "path": "/api/indicator_data/{id}/", "label": _("Update indicator value"), "scope": _("Write")},
        {"method": "DELETE", "path": "/api/indicator_data/{id}/", "label": _("Delete indicator value"), "scope": _("Write")},
        {"method": "GET", "path": "/api/indicators_archive/", "label": _("List indicator archives"), "scope": _("Read")},
        {"method": "GET", "path": "/api/data_sources/", "label": _("List data sources"), "scope": _("Read")},
        {"method": "GET", "path": "/api/measure_types/", "label": _("List measure types"), "scope": _("Read")},
        {"method": "POST", "path": "/api/auth-token/", "label": _("Generate DRF auth token"), "scope": _("Write")},
    ]

    context = admin.site.each_context(request)
    context.update(
        {
            "title": _("API tokens"),
            "subtitle": _("Create tokens, review active access, and copy API examples for the Django repository."),
            "plain_token": plain_token,
            "tokens": tokens,
            "token_count": token_queryset.count(),
            "endpoints": endpoints,
            "api_root": api_root,
            "curl_get": f'curl -H "Authorization: Token {token_example}" "{api_root}indicator_data/"',
            "curl_post": (
                f'curl -X POST "{api_root}indicator_data/" '
                f'-H "Authorization: Token {token_example}" '
                '-H "Content-Type: application/json" '
                "-d \"{\\\"indicator\\\":1,\\\"location\\\":1,\\\"categoryoption\\\":1,\\\"datasource\\\":1,\\\"measuremethod\\\":1,\\\"value_received\\\":120,\\\"start_period\\\":2024,\\\"end_period\\\":2024}\""
            ),
        }
    )
    return render(request, "admin/aho_api_tokens_page.html", context)
