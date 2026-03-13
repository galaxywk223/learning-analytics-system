from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from app.models import AIChatMessage, AIInsight, Setting, Stage
from app.services.chart_service import get_chart_forecast_status_for_user

from .aggregation import _aggregate_learning_data
from .date_ranges import _format_period_label, _get_date_range_for_scope, _get_next_range, _get_prev_range

ALLOWED_CHAT_MODULES = {
    "trend_daily_detail",
    "trend_weekly_detail",
    "forecast_detail",
    "category_duration_detail",
    "category_efficiency_detail",
    "task_focus_detail",
    "stage_timeline_detail",
    "countdown_detail",
    "recent_ai_history_detail",
}

ALLOWED_TIME_WINDOWS = {
    "current_day",
    "current_week",
    "previous_week",
    "current_month",
    "previous_month",
    "last_30_days",
    "last_90_days",
    "current_stage",
    "previous_stage",
}


def _round_number(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 2)
    return value


def _build_comparison(current_stats: dict[str, Any], previous_stats: dict[str, Any] | None) -> dict[str, Any]:
    if not previous_stats:
        return {}

    def _diff(current: float | int | None, previous: float | int | None) -> dict[str, Any]:
        current_value = float(current or 0)
        previous_value = float(previous or 0)
        delta = current_value - previous_value
        delta_pct = None
        if previous_value:
            delta_pct = round(delta / previous_value * 100, 1)
        return {
            "current": _round_number(current_value),
            "previous": _round_number(previous_value),
            "delta": _round_number(delta),
            "delta_pct": delta_pct,
        }

    return {
        "total_hours": _diff(
            current_stats.get("total_hours"),
            previous_stats.get("total_hours"),
        ),
        "average_efficiency": _diff(
            current_stats.get("average_efficiency"),
            previous_stats.get("average_efficiency"),
        ),
        "active_ratio": _diff(
            current_stats.get("active_ratio"),
            previous_stats.get("active_ratio"),
        ),
    }


def _build_trend_summary(stats: dict[str, Any]) -> dict[str, Any]:
    daily_stats = list(stats.get("daily_stats") or [])
    if not daily_stats:
        return {
            "last_7_days": [],
            "duration_avg_last_7": 0,
            "efficiency_avg_last_7": None,
        }

    last_7_days = daily_stats[-7:]
    durations = [float(item.get("duration_minutes") or 0) / 60.0 for item in last_7_days]
    efficiencies = [
        float(item["efficiency"])
        for item in last_7_days
        if item.get("efficiency") is not None
    ]
    return {
        "last_7_days": [
            {
                "date": item.get("date"),
                "hours": round(float(item.get("duration_minutes") or 0) / 60.0, 2),
                "efficiency": item.get("efficiency"),
            }
            for item in last_7_days
        ],
        "duration_avg_last_7": round(sum(durations) / max(len(durations), 1), 2),
        "efficiency_avg_last_7": (
            round(sum(efficiencies) / len(efficiencies), 2) if efficiencies else None
        ),
    }


def _build_weekly_detail(stats: dict[str, Any]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"period": "", "hours": 0.0, "efficiency_values": []}
    )
    for item in list(stats.get("daily_stats") or []):
        item_date = date.fromisoformat(item["date"])
        week_start = item_date - timedelta(days=item_date.weekday())
        week_end = week_start + timedelta(days=6)
        label = f"{week_start.isoformat()} 至 {week_end.isoformat()}"
        bucket = buckets[label]
        bucket["period"] = label
        bucket["hours"] += float(item.get("duration_minutes") or 0) / 60.0
        if item.get("efficiency") is not None:
            bucket["efficiency_values"].append(float(item["efficiency"]))

    weekly_rows = []
    for label, bucket in sorted(buckets.items()):
        efficiency_values = bucket.pop("efficiency_values")
        weekly_rows.append(
            {
                "period": label,
                "hours": round(bucket["hours"], 2),
                "average_efficiency": (
                    round(sum(efficiency_values) / len(efficiency_values), 2)
                    if efficiency_values
                    else None
                ),
            }
        )
    return weekly_rows[-12:]


def _build_stage_timeline(user_id: int) -> list[dict[str, Any]]:
    stages = Stage.query.filter_by(user_id=user_id).order_by(Stage.start_date.asc()).all()
    timeline: list[dict[str, Any]] = []
    for index, stage in enumerate(stages):
        next_stage = stages[index + 1] if index + 1 < len(stages) else None
        timeline.append(
            {
                "id": stage.id,
                "name": stage.name,
                "start_date": stage.start_date.isoformat() if stage.start_date else None,
                "next_stage_name": next_stage.name if next_stage else None,
                "next_stage_start": (
                    next_stage.start_date.isoformat() if next_stage and next_stage.start_date else None
                ),
            }
        )
    return timeline


def _build_recent_history(user_id: int, session_id: int | None = None) -> list[dict[str, Any]]:
    messages_query = AIChatMessage.query.filter(
        AIChatMessage.user_id == user_id,
        AIChatMessage.role == "assistant",
    )
    if session_id:
        messages_query = messages_query.filter(AIChatMessage.session_id == session_id)
    messages = (
        messages_query.order_by(AIChatMessage.created_at.desc()).limit(4).all()
    )
    if messages:
        return [
            {
                "content": message.content[:240],
                "created_at": message.created_at.isoformat() if message.created_at else None,
                "scope": message.scope,
            }
            for message in reversed(messages)
        ]

    legacy_items = (
        AIInsight.query.filter(AIInsight.user_id == user_id)
        .order_by(AIInsight.created_at.desc())
        .limit(3)
        .all()
    )
    return [
        {
            "content": item.output_text[:240],
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "scope": item.scope,
        }
        for item in reversed(legacy_items)
    ]


def _build_settings_digest(user_id: int) -> dict[str, Any]:
    settings = Setting.query.filter(Setting.user_id == user_id).all()
    allowed_prefixes = ("study_", "learning_", "focus_", "countdown_", "theme")
    result: dict[str, Any] = {}
    for item in settings:
        if item.key.startswith(allowed_prefixes):
            result[item.key] = item.value
    return result


def _find_stage_windows(user_id: int) -> tuple[Stage | None, Stage | None]:
    stages = Stage.query.filter_by(user_id=user_id).order_by(Stage.start_date.desc()).all()
    current_stage = stages[0] if stages else None
    previous_stage = stages[1] if len(stages) > 1 else None
    return current_stage, previous_stage


def _build_context_bundle_for_dates(
    user_id: int,
    *,
    scope: str,
    start: date,
    end: date,
    period_label: str,
    stage: Stage | None = None,
    next_period_label: str | None = None,
    session_id: int | None = None,
) -> dict[str, Any]:
    stats = _aggregate_learning_data(user_id, start, end, stage)
    prev_stats = None
    if scope != "stage":
      prev_start, prev_end = _get_prev_range(scope, start, end)
      if prev_start and prev_end:
          prev_stats = _aggregate_learning_data(user_id, prev_start, prev_end, None)
    default_context = {
        "scope": scope,
        "period_label": period_label,
        "next_period_label": next_period_label,
        "current_stage": stage.name if stage else None,
        "overview_metrics": {
            "total_hours": stats.get("total_hours"),
            "total_sessions": stats.get("total_sessions"),
            "average_efficiency": stats.get("average_efficiency"),
            "average_mood": stats.get("average_mood"),
            "active_ratio": stats.get("active_ratio"),
            "streak_current": stats.get("streak_current"),
            "streak_longest": stats.get("streak_longest"),
        },
        "comparison": _build_comparison(stats, prev_stats),
        "trend_summary": _build_trend_summary(stats),
        "category_focus": list(stats.get("category_stats") or [])[:5],
        "task_focus": list(stats.get("top_tasks") or [])[:5],
        "countdown_context": stats.get("countdown_context") or {},
        "settings_digest": _build_settings_digest(user_id),
        "stage_timeline": _build_stage_timeline(user_id),
        "recent_ai_history": _build_recent_history(user_id, session_id=session_id),
    }
    return {
        "meta": {
            "scope": scope,
            "period_label": period_label,
            "next_period_label": next_period_label,
            "stage_name": stage.name if stage else None,
            "start_date": start,
            "end_date": end,
            "scope_reference": stage.id if stage else None,
            "date_reference": start if scope != "stage" else None,
        },
        "stats": stats,
        "prev_stats": prev_stats,
        "default_context": default_context,
    }


def build_global_chat_context(
    user_id: int,
    *,
    session_id: int | None = None,
) -> dict[str, Any]:
    today = date.today()
    current_stage, _ = _find_stage_windows(user_id)
    day_bundle = build_default_chat_context(user_id, "day", today.isoformat(), None, session_id=session_id)
    week_bundle = build_default_chat_context(user_id, "week", today.isoformat(), None, session_id=session_id)
    month_bundle = build_default_chat_context(user_id, "month", today.isoformat(), None, session_id=session_id)
    stage_bundle = (
        build_default_chat_context(
            user_id,
            "stage",
            None,
            current_stage.id,
            session_id=session_id,
        )
        if current_stage
        else None
    )
    forecast_status = get_chart_forecast_status_for_user(user_id)
    return {
        "meta": {
            "scope": "global",
            "period_label": "全局概览",
            "next_period_label": None,
            "stage_name": current_stage.name if current_stage else None,
            "scope_reference": current_stage.id if current_stage else None,
            "date_reference": today,
        },
        "stats": week_bundle["stats"],
        "prev_stats": week_bundle["prev_stats"],
        "default_context": {
            "scope": "global",
            "period_label": "全局概览",
            "current_stage": current_stage.name if current_stage else None,
            "overview": {
                "today": day_bundle["default_context"],
                "this_week": week_bundle["default_context"],
                "this_month": month_bundle["default_context"],
                "current_stage": stage_bundle["default_context"] if stage_bundle else None,
            },
            "forecast_summary": forecast_status,
            "stage_timeline": _build_stage_timeline(user_id),
            "settings_digest": _build_settings_digest(user_id),
            "recent_ai_history": _build_recent_history(user_id, session_id=session_id),
        },
    }


def build_default_chat_context(
    user_id: int,
    scope: str,
    date_str: str | None,
    stage_id: int | None,
    *,
    session_id: int | None = None,
) -> dict[str, Any]:
    start, end, stage = _get_date_range_for_scope(scope, date_str, stage_id, user_id)
    stats = _aggregate_learning_data(user_id, start, end, stage)
    prev_start, prev_end = _get_prev_range(scope, start, end)
    prev_stats = None
    if prev_start and prev_end and scope != "stage":
        prev_stats = _aggregate_learning_data(user_id, prev_start, prev_end, None)
    next_start, next_end, next_stage_name = _get_next_range(scope, start, end, stage, user_id)
    period_label = _format_period_label(scope, start, end)
    next_period_label = _format_period_label(scope, next_start, next_end)
    if scope == "stage" and next_stage_name:
        next_period_label = f"阶段：{next_stage_name}"

    forecast_status = get_chart_forecast_status_for_user(user_id)
    forecast_summary = {}
    for dataset_key, forecast in (forecast_status.get("forecasts") or {}).items():
        forecast_summary[dataset_key] = {
            "status": forecast.get("status"),
            "available": forecast.get("available"),
            "model_name": forecast.get("model_name"),
            "validation_wape": forecast.get("validation_wape"),
            "next_label": (forecast.get("labels") or [None])[0],
            "next_prediction": (forecast.get("prediction") or [None])[0],
        }

    default_context = {
        "scope": scope,
        "period_label": period_label,
        "next_period_label": next_period_label,
        "current_stage": stage.name if stage else None,
        "overview_metrics": {
            "total_hours": stats.get("total_hours"),
            "total_sessions": stats.get("total_sessions"),
            "average_efficiency": stats.get("average_efficiency"),
            "average_mood": stats.get("average_mood"),
            "active_ratio": stats.get("active_ratio"),
            "streak_current": stats.get("streak_current"),
            "streak_longest": stats.get("streak_longest"),
        },
        "comparison": _build_comparison(stats, prev_stats),
        "trend_summary": _build_trend_summary(stats),
        "forecast_summary": forecast_summary,
        "category_focus": list(stats.get("category_stats") or [])[:5],
        "task_focus": list(stats.get("top_tasks") or [])[:5],
        "countdown_context": stats.get("countdown_context") or {},
        "settings_digest": _build_settings_digest(user_id),
        "stage_timeline": _build_stage_timeline(user_id),
        "recent_ai_history": _build_recent_history(user_id, session_id=session_id),
    }

    return {
        "meta": {
            "scope": scope,
            "period_label": period_label,
            "next_period_label": next_period_label,
            "stage_name": stage.name if stage else None,
            "start_date": start,
            "end_date": end,
            "next_start": next_start,
            "next_end": next_end,
            "scope_reference": stage.id if stage else None,
            "date_reference": start if scope != "stage" else None,
        },
        "stats": stats,
        "prev_stats": prev_stats,
        "default_context": default_context,
    }


def normalize_requested_windows(windows: list[str] | None) -> list[str]:
    if not windows:
        return []
    result: list[str] = []
    for item in windows:
        key = str(item or "").strip()
        if key in ALLOWED_TIME_WINDOWS and key not in result:
            result.append(key)
    return result


def build_window_context(
    user_id: int,
    window_key: str,
    *,
    session_id: int | None = None,
) -> dict[str, Any] | None:
    today = date.today()
    current_stage, previous_stage = _find_stage_windows(user_id)

    if window_key == "current_day":
        return build_default_chat_context(user_id, "day", today.isoformat(), None, session_id=session_id)
    if window_key == "current_week":
        return build_default_chat_context(user_id, "week", today.isoformat(), None, session_id=session_id)
    if window_key == "previous_week":
        return build_default_chat_context(
            user_id,
            "week",
            (today - timedelta(days=7)).isoformat(),
            None,
            session_id=session_id,
        )
    if window_key == "current_month":
        return build_default_chat_context(user_id, "month", today.isoformat(), None, session_id=session_id)
    if window_key == "previous_month":
        return build_default_chat_context(
            user_id,
            "month",
            (today.replace(day=1) - timedelta(days=1)).isoformat(),
            None,
            session_id=session_id,
        )
    if window_key == "last_30_days":
        start = today - timedelta(days=29)
        return _build_context_bundle_for_dates(
            user_id,
            scope="custom",
            start=start,
            end=today,
            period_label=f"近30天（{start.isoformat()} 至 {today.isoformat()}）",
            session_id=session_id,
        )
    if window_key == "last_90_days":
        start = today - timedelta(days=89)
        return _build_context_bundle_for_dates(
            user_id,
            scope="custom",
            start=start,
            end=today,
            period_label=f"近90天（{start.isoformat()} 至 {today.isoformat()}）",
            session_id=session_id,
        )
    if window_key == "current_stage" and current_stage:
        return build_default_chat_context(
            user_id,
            "stage",
            None,
            current_stage.id,
            session_id=session_id,
        )
    if window_key == "previous_stage" and previous_stage:
        return build_default_chat_context(
            user_id,
            "stage",
            None,
            previous_stage.id,
            session_id=session_id,
        )
    return None


def normalize_requested_modules(modules: list[str] | None) -> list[str]:
    if not modules:
        return []
    result: list[str] = []
    for item in modules:
        key = str(item or "").strip()
        if key in ALLOWED_CHAT_MODULES and key not in result:
            result.append(key)
    return result


def build_requested_modules(
    user_id: int,
    context_bundle: dict[str, Any],
    requested_modules: list[str],
    *,
    requested_windows: list[str] | None = None,
    session_id: int | None = None,
) -> dict[str, Any]:
    modules: dict[str, Any] = {}
    normalized_windows = normalize_requested_windows(requested_windows)
    if normalized_windows:
        window_payload: dict[str, Any] = {}
        for window_key in normalized_windows:
            bundle = build_window_context(user_id, window_key, session_id=session_id)
            if not bundle:
                continue
            stats = bundle["stats"]
            window_modules: dict[str, Any] = {
                "period_label": bundle["meta"]["period_label"],
                "scope": bundle["meta"]["scope"],
                "stage_name": bundle["meta"].get("stage_name"),
            }
            for key in normalize_requested_modules(requested_modules):
                if key == "trend_daily_detail":
                    window_modules[key] = list(stats.get("daily_stats") or [])[-21:]
                elif key == "trend_weekly_detail":
                    window_modules[key] = _build_weekly_detail(stats)
                elif key == "forecast_detail":
                    window_modules[key] = get_chart_forecast_status_for_user(user_id)
                elif key == "category_duration_detail":
                    window_modules[key] = list(stats.get("category_stats") or [])
                elif key == "category_efficiency_detail":
                    baseline = stats.get("efficiency_baseline") or {}
                    window_modules[key] = {
                        "average_efficiency": stats.get("average_efficiency"),
                        "baseline": baseline,
                        "top_categories": list(stats.get("category_stats") or [])[:5],
                    }
                elif key == "task_focus_detail":
                    window_modules[key] = list(stats.get("top_tasks") or [])
                elif key == "stage_timeline_detail":
                    window_modules[key] = _build_stage_timeline(user_id)
                elif key == "countdown_detail":
                    window_modules[key] = stats.get("countdown_context") or {}
                elif key == "recent_ai_history_detail":
                    window_modules[key] = _build_recent_history(user_id, session_id=session_id)
            window_payload[window_key] = window_modules
        return window_payload

    stats = context_bundle["stats"]
    for key in normalize_requested_modules(requested_modules):
        if key == "trend_daily_detail":
            modules[key] = list(stats.get("daily_stats") or [])[-21:]
        elif key == "trend_weekly_detail":
            modules[key] = _build_weekly_detail(stats)
        elif key == "forecast_detail":
            modules[key] = get_chart_forecast_status_for_user(user_id)
        elif key == "category_duration_detail":
            modules[key] = list(stats.get("category_stats") or [])
        elif key == "category_efficiency_detail":
            baseline = stats.get("efficiency_baseline") or {}
            modules[key] = {
                "average_efficiency": stats.get("average_efficiency"),
                "baseline": baseline,
                "top_categories": list(stats.get("category_stats") or [])[:5],
            }
        elif key == "task_focus_detail":
            modules[key] = list(stats.get("top_tasks") or [])
        elif key == "stage_timeline_detail":
            modules[key] = _build_stage_timeline(user_id)
        elif key == "countdown_detail":
            modules[key] = stats.get("countdown_context") or {}
        elif key == "recent_ai_history_detail":
            modules[key] = _build_recent_history(user_id, session_id=session_id)
    return modules
