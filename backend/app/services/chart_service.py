"""
图表统计服务
"""

import collections
import copy
import hashlib
import json
import math
import os
import threading
import time
from datetime import date, datetime, timedelta
from typing import Any, Sequence, TypedDict
from sqlalchemy import func, desc
import numpy as np
from flask import current_app, has_app_context

from app import db
from app.models import Stage, LogEntry, DailyData, Category, SubCategory
from .forecast_service import DAILY_CONFIG, WEEKLY_CONFIG, build_trend_forecasts
from .helpers import get_custom_week_info

_OVERVIEW_CACHE_TTL_SECONDS = 20.0
_PENDING_OVERVIEW_CACHE_TTL_SECONDS = 3.0
_FORECAST_CACHE_TTL_SECONDS = 15 * 60.0
_overview_cache_lock = threading.Lock()
_overview_cache: dict[int, tuple[float, dict]] = {}
_overview_inflight: dict[int, threading.Event] = {}
_forecast_cache_lock = threading.Lock()
_forecast_cache: dict[int, dict[str, Any]] = {}
_forecast_inflight: dict[int, threading.Event] = {}
_FORECAST_DATASET_KEYS = (
    "daily_duration_data",
    "daily_efficiency_data",
    "weekly_duration_data",
    "weekly_efficiency_data",
)
_PENDING_FORECAST_REASON = "预测计算中，请稍后刷新"
_FORECAST_ERROR_REASON = "预测生成失败，请稍后重试"
_FORECAST_CACHE_DIRNAME = "chart_forecasts"


def _calculate_sma(
    data: Sequence[float | None], window_size: int = 7
) -> list[float | None]:
    """计算简单移动平均线，能正确处理None/NaN值"""
    if not data or window_size <= 1:
        return [None] * len(data)

    numeric_data = [float(v) if v is not None else np.nan for v in data]

    if len(numeric_data) < window_size:
        return [None] * len(numeric_data)

    sma_values: list[float | None] = []
    window: collections.deque[float] = collections.deque(maxlen=window_size)
    for i, value in enumerate(numeric_data):
        window.append(value)
        if i < window_size - 1:
            sma_values.append(None)
        else:
            valid_values = [v for v in window if not np.isnan(v)]
            sma = sum(valid_values) / len(valid_values) if valid_values else None
            sma_values.append(round(sma, 2) if sma is not None else None)

    return sma_values


def _calculate_kpis(user_id, stage_ids):
    """为用户计算关键性能指标(KPIs)"""
    kpis = {}

    total_duration_minutes = (
        db.session.query(func.sum(LogEntry.actual_duration))
        .filter(LogEntry.stage_id.in_(stage_ids))
        .scalar()
        or 0
    )
    total_days_with_logs = (
        db.session.query(func.count(func.distinct(LogEntry.log_date)))
        .filter(LogEntry.stage_id.in_(stage_ids))
        .scalar()
        or 0
    )
    kpis["avg_daily_minutes"] = (
        round(total_duration_minutes / total_days_with_logs, 1)
        if total_days_with_logs > 0
        else 0
    )

    top_efficiency_day = (
        DailyData.query.join(Stage)
        .filter(Stage.user_id == user_id)
        .order_by(desc(DailyData.efficiency))
        .first()
    )
    if top_efficiency_day and top_efficiency_day.efficiency is not None:
        kpis["efficiency_star"] = (
            f"{top_efficiency_day.log_date.strftime('%Y-%m-%d')} (效率: {top_efficiency_day.efficiency:.1f})"
        )
    else:
        kpis["efficiency_star"] = "无足够数据"

    today = date.today()
    start_of_this_week = today - timedelta(days=today.weekday())
    end_of_this_week = start_of_this_week + timedelta(days=6)
    logs_this_week = (
        db.session.query(func.sum(LogEntry.actual_duration))
        .join(Stage)
        .filter(
            Stage.user_id == user_id,
            LogEntry.log_date.between(start_of_this_week, end_of_this_week),
        )
        .scalar()
        or 0
    )

    start_of_last_week = start_of_this_week - timedelta(days=7)
    end_of_last_week = start_of_this_week - timedelta(days=1)
    logs_last_week = (
        db.session.query(func.sum(LogEntry.actual_duration))
        .join(Stage)
        .filter(
            Stage.user_id == user_id,
            LogEntry.log_date.between(start_of_last_week, end_of_last_week),
        )
        .scalar()
        or 0
    )

    if logs_last_week > 0:
        percentage_change = ((logs_this_week - logs_last_week) / logs_last_week) * 100
        kpis["weekly_trend"] = (
            f"{'+' if percentage_change >= 0 else ''}{percentage_change:.0f}%"
        )
    elif logs_this_week > 0:
        kpis["weekly_trend"] = "新开始"
    else:
        kpis["weekly_trend"] = "无对比数据"

    return kpis


class _WeekBucket(TypedDict):
    duration: float
    efficiency: float | None
    days: int


class _CategorySub(TypedDict):
    name: str
    duration: float


class _CategoryAgg(TypedDict):
    total: float
    subs: list[_CategorySub]


def _force_sync_forecast_mode() -> bool:
    if not has_app_context():
        return False
    explicit = current_app.config.get("CHART_FORECAST_SYNC_MODE")
    if explicit is not None:
        return bool(explicit)
    return bool(current_app.config.get("TESTING"))


def _utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _today_cache_key() -> str:
    return date.today().isoformat()


def _build_default_forecast(
    *,
    status: str = "unavailable",
    reason: str = "",
) -> dict[str, Any]:
    return {
        "labels": [],
        "prediction": [],
        "lower": [],
        "upper": [],
        "model_name": None,
        "history_points": 0,
        "horizon": 0,
        "trained_on": "all_history",
        "confidence_level": 0.8,
        "accuracy_threshold": 0.4,
        "selection_strategy": "lowest_wape_then_rmse_with_weighted_blend",
        "validation_wape": None,
        "validation_rmse": None,
        "baseline_wape": None,
        "baseline_rmse": None,
        "model_candidates": [],
        "available": False,
        "reason": reason,
        "status": status,
    }


def _deep_round(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, list):
        return [_deep_round(item) for item in value]
    if isinstance(value, tuple):
        return [_deep_round(item) for item in value]
    if isinstance(value, dict):
        return {key: _deep_round(item) for key, item in value.items()}
    return value


def _build_forecast_signature(
    trend_data: dict[str, Any],
    *,
    global_start_date: date,
    last_log_date: date,
) -> str:
    signature_payload: dict[str, Any] = {
        "global_start_date": global_start_date.isoformat(),
    }
    # Only hash stable training inputs. Ongoing buckets are display-only and
    # should not invalidate the trained forecast within the same day/week.
    del last_log_date
    for dataset_key in _FORECAST_DATASET_KEYS:
        dataset = trend_data.get(dataset_key) or {}
        signature_payload[dataset_key] = _deep_round(
            {
                "training_labels": dataset.get("training_labels") or [],
                "training_actuals": dataset.get("training_actuals") or [],
                "training_stage_features": dataset.get("training_stage_features") or [],
                "future_stage_features": dataset.get("future_stage_features") or [],
            }
        )
    digest_source = json.dumps(
        signature_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha1(digest_source.encode("utf-8")).hexdigest()


def _attach_forecast_bundle(
    payload: dict[str, Any],
    forecast_bundle: dict[str, Any] | None,
) -> dict[str, Any]:
    for dataset_key in _FORECAST_DATASET_KEYS:
        dataset = payload.get(dataset_key)
        if not isinstance(dataset, dict):
            continue
        forecast = (forecast_bundle or {}).get(dataset_key)
        dataset["forecast"] = copy.deepcopy(
            forecast if isinstance(forecast, dict) else _build_default_forecast()
        )
    return payload


def _build_forecast_status_payload(
    *,
    state: str,
    signature: str | None,
    message: str,
    updated_at: str | None,
    trained_for_date: str | None = None,
) -> dict[str, Any]:
    return {
        "state": state,
        "signature": signature,
        "message": message,
        "updated_at": updated_at,
        "trained_for_date": trained_for_date,
    }


def _build_pending_forecast_bundle() -> dict[str, dict[str, Any]]:
    return {
        dataset_key: _build_default_forecast(
            status="pending",
            reason=_PENDING_FORECAST_REASON,
        )
        for dataset_key in _FORECAST_DATASET_KEYS
    }


def _forecast_cache_dir() -> str:
    instance_path = current_app.instance_path if has_app_context() else os.getcwd()
    cache_dir = os.path.join(instance_path, _FORECAST_CACHE_DIRNAME)
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def _forecast_cache_file(user_id: int) -> str:
    return os.path.join(_forecast_cache_dir(), f"user_{user_id}.json")


def _load_persisted_forecast_entry(user_id: int) -> dict[str, Any] | None:
    cache_file = _forecast_cache_file(user_id)
    if not os.path.exists(cache_file):
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as fp:
            payload = json.load(fp)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    payload["expires_at"] = time.monotonic() + _FORECAST_CACHE_TTL_SECONDS
    return payload


def _persist_forecast_entry(
    user_id: int,
    entry: dict[str, Any],
    *,
    instance_path: str | None = None,
    logger: Any | None = None,
    testing: bool = False,
) -> None:
    if testing:
        return
    base_dir = instance_path or (current_app.instance_path if has_app_context() else os.getcwd())
    cache_dir = os.path.join(base_dir, _FORECAST_CACHE_DIRNAME)
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"user_{user_id}.json")
    serializable = copy.deepcopy(entry)
    serializable.pop("expires_at", None)
    try:
        with open(cache_file, "w", encoding="utf-8") as fp:
            json.dump(serializable, fp, ensure_ascii=False)
    except OSError:
        if logger is not None:
            logger.warning(
                "Failed to persist chart forecast cache for user %s",
                user_id,
            )


def _clear_persisted_forecast_entry(user_id: int) -> None:
    cache_file = _forecast_cache_file(user_id)
    try:
        if os.path.exists(cache_file):
            os.remove(cache_file)
    except OSError:
        if has_app_context():
            current_app.logger.warning(
                "Failed to remove chart forecast cache for user %s",
                user_id,
            )


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _is_incomplete_daily_bucket(bucket_date: date, today: date) -> bool:
    return bucket_date == today


def _is_incomplete_weekly_bucket(
    bucket_start: date,
    bucket_end: date,
    *,
    today: date,
) -> bool:
    return bucket_start <= today <= bucket_end and today < bucket_end


def _build_stage_snapshot_resolver(all_stages):
    sorted_stages = sorted(all_stages, key=lambda stage: stage.start_date)
    total_stages = len(sorted_stages)

    def _resolve(target_date: date) -> list[float]:
        current_index = 0
        for idx, stage in enumerate(sorted_stages):
            if stage.start_date <= target_date:
                current_index = idx
            else:
                break
        current_stage = sorted_stages[current_index]
        stage_age_days = max((target_date - current_stage.start_date).days, 0)
        stage_index_norm = (
            current_index / max(total_stages - 1, 1) if total_stages > 1 else 0.0
        )
        stage_start_flag = 1.0 if target_date == current_stage.start_date else 0.0
        return [
            round(float(stage_age_days), 2),
            round(float(stage_index_norm), 4),
            stage_start_flag,
        ]

    return _resolve


def _prepare_trend_data(user_id, all_stages, all_logs):
    """准备每日和每周趋势的数据结构"""
    first_log_date = min(log.log_date for log in all_logs)
    last_log_date = max(log.log_date for log in all_logs)
    today = date.today()
    global_start_date = all_stages[0].start_date
    stage_ids = [s.id for s in all_stages]

    date_range = [
        first_log_date + timedelta(days=x)
        for x in range((last_log_date - first_log_date).days + 1)
    ]
    resolve_stage_snapshot = _build_stage_snapshot_resolver(all_stages)
    daily_labels = [d.isoformat() for d in date_range]
    daily_duration_map = {
        d[0]: d[1]
        for d in db.session.query(LogEntry.log_date, func.sum(LogEntry.actual_duration))
        .filter(LogEntry.stage_id.in_(stage_ids))
        .group_by(LogEntry.log_date)
        .all()
    }
    daily_durations = [
        round((daily_duration_map.get(d, 0) or 0) / 60, 2) for d in date_range
    ]
    daily_efficiency_map = {
        d.log_date: d.efficiency
        for d in DailyData.query.join(Stage).filter(Stage.user_id == user_id).all()
    }
    daily_stage_feature_map = {
        current_date: resolve_stage_snapshot(current_date) for current_date in date_range
    }
    daily_efficiencies = [daily_efficiency_map.get(d) for d in date_range]
    daily_incomplete = bool(date_range) and _is_incomplete_daily_bucket(
        date_range[-1], today
    )
    daily_training_labels = (
        daily_labels[:-1] if daily_incomplete else list(daily_labels)
    )
    daily_training_dates = date_range[:-1] if daily_incomplete else list(date_range)
    daily_training_durations = (
        daily_durations[:-1] if daily_incomplete else list(daily_durations)
    )
    daily_training_efficiencies = (
        daily_efficiencies[:-1] if daily_incomplete else list(daily_efficiencies)
    )
    daily_training_stage_features = [
        daily_stage_feature_map[current_date] for current_date in daily_training_dates
    ]
    daily_live_duration = daily_durations[-1] if daily_incomplete else None
    daily_live_efficiency = daily_efficiencies[-1] if daily_incomplete else None

    weekly_data: dict[tuple[int, int], _WeekBucket] = collections.defaultdict(
        lambda: {"duration": 0.0, "efficiency": None, "days": 0}
    )
    weekly_stage_feature_accumulator: dict[tuple[int, int], list[list[float]]] = (
        collections.defaultdict(list)
    )
    for d in date_range:
        year, week_num = get_custom_week_info(d, global_start_date)
        weekly_data[(year, week_num)]["duration"] += float(
            daily_duration_map.get(d) or 0
        )
        weekly_data[(year, week_num)]["days"] += 1
        day_efficiency = daily_efficiency_map.get(d)
        if day_efficiency is None:
            day_efficiency = 0.0
        current_efficiency = weekly_data[(year, week_num)]["efficiency"] or 0.0
        weekly_data[(year, week_num)]["efficiency"] = current_efficiency + float(
            day_efficiency
        )
        weekly_stage_feature_accumulator[(year, week_num)].append(
            daily_stage_feature_map[d]
        )

    sorted_week_keys = sorted(weekly_data.keys())
    weekly_labels = [f"{k[0]}-W{k[1]:02}" for k in sorted_week_keys]
    weekly_durations = []
    weekly_efficiencies = []
    weekly_duration_totals = []
    weekly_elapsed_days = []
    weekly_stage_features = []
    for year, week_num in sorted_week_keys:
        duration = weekly_data[(year, week_num)]["duration"]
        days = weekly_data[(year, week_num)]["days"] or 0
        week_anchor = next(
            d
            for d in date_range
            if get_custom_week_info(d, global_start_date) == (year, week_num)
        )
        bucket_start = _week_start(week_anchor)
        bucket_end = bucket_start + timedelta(days=6)
        elapsed_days = (
            (today - bucket_start).days + 1
            if _is_incomplete_weekly_bucket(bucket_start, bucket_end, today=today)
            else days
        )
        elapsed_days = max(1, min(elapsed_days, 7))
        weekly_elapsed_days.append(elapsed_days)
        weekly_duration_totals.append(round(duration / 60, 2))
        weekly_durations.append(round(duration / 60 / elapsed_days, 2))
        efficiency_total = weekly_data[(year, week_num)]["efficiency"] or 0.0
        weekly_efficiencies.append(round(efficiency_total / elapsed_days, 2))
        stage_rows = weekly_stage_feature_accumulator[(year, week_num)]
        avg_stage_age_days = (
            sum(row[0] for row in stage_rows) / len(stage_rows) if stage_rows else 0.0
        )
        avg_stage_index = (
            sum(row[1] for row in stage_rows) / len(stage_rows) if stage_rows else 0.0
        )
        stage_reset_flag = max((row[2] for row in stage_rows), default=0.0)
        weekly_stage_features.append(
            [
                round(avg_stage_age_days / 7.0, 2),
                round(avg_stage_index, 4),
                stage_reset_flag,
            ]
        )

    weekly_incomplete = False
    weekly_live_duration = None
    weekly_live_efficiency = None
    weekly_training_labels = list(weekly_labels)
    weekly_training_duration_totals = list(weekly_duration_totals)
    weekly_training_efficiencies = list(weekly_efficiencies)
    if sorted_week_keys:
        last_year, last_week = sorted_week_keys[-1]
        last_anchor = next(
            d
            for d in reversed(date_range)
            if get_custom_week_info(d, global_start_date) == (last_year, last_week)
        )
        last_bucket_start = _week_start(last_anchor)
        last_bucket_end = last_bucket_start + timedelta(days=6)
        weekly_incomplete = _is_incomplete_weekly_bucket(
            last_bucket_start,
            last_bucket_end,
            today=today,
        )
        if weekly_incomplete:
            weekly_live_duration = weekly_durations[-1]
            weekly_live_efficiency = weekly_efficiencies[-1]
            weekly_training_labels = weekly_labels[:-1]
            weekly_training_duration_totals = weekly_duration_totals[:-1]
            weekly_training_efficiencies = weekly_efficiencies[:-1]

    weekly_training_stage_features = (
        weekly_stage_features[:-1] if weekly_incomplete else list(weekly_stage_features)
    )

    daily_future_start = date_range[-1] if daily_incomplete else (date_range[-1] + timedelta(days=1))
    daily_future_stage_features = [
        resolve_stage_snapshot(daily_future_start + timedelta(days=offset))
        for offset in range(DAILY_CONFIG.horizon)
    ]

    # Keep weekly future features stable for the current day even if the user
    # starts logging into the current week for the first time.
    weekly_reference_date = today
    weekly_future_stage_features = []
    for offset in range(WEEKLY_CONFIG.horizon):
        target_date = weekly_reference_date + timedelta(days=offset * 7)
        stage_snapshot = resolve_stage_snapshot(target_date)
        weekly_future_stage_features.append(
            [
                round(stage_snapshot[0] / 7.0, 2),
                stage_snapshot[1],
                stage_snapshot[2],
            ]
        )

    return {
        "weekly_duration_data": {
            "labels": weekly_labels,
            "actuals": weekly_durations,
            "trends": _calculate_sma(weekly_durations, 3),
            "training_labels": weekly_training_labels,
            "training_actuals": weekly_training_duration_totals,
            "training_stage_features": weekly_training_stage_features,
            "future_stage_features": weekly_future_stage_features,
            "ongoing_label": weekly_labels[-1] if weekly_incomplete else None,
            "ongoing_value": weekly_live_duration,
            "ongoing": weekly_incomplete,
            "debug_today": today.isoformat(),
            "debug_last_log_date": last_log_date.isoformat(),
            "debug_training_last_label": weekly_training_labels[-1] if weekly_training_labels else None,
        },
        "weekly_efficiency_data": {
            "labels": weekly_labels,
            "actuals": weekly_efficiencies,
            "trends": _calculate_sma(weekly_efficiencies, 3),
            "training_labels": weekly_training_labels,
            "training_actuals": weekly_training_efficiencies,
            "training_stage_features": weekly_training_stage_features,
            "future_stage_features": weekly_future_stage_features,
            "ongoing_label": weekly_labels[-1] if weekly_incomplete else None,
            "ongoing_value": weekly_live_efficiency,
            "ongoing": weekly_incomplete,
            "debug_today": today.isoformat(),
            "debug_last_log_date": last_log_date.isoformat(),
            "debug_training_last_label": weekly_training_labels[-1] if weekly_training_labels else None,
        },
        "daily_duration_data": {
            "labels": daily_labels,
            "actuals": daily_durations,
            "trends": _calculate_sma(daily_durations, 7),
            "training_labels": daily_training_labels,
            "training_actuals": daily_training_durations,
            "training_stage_features": daily_training_stage_features,
            "future_stage_features": daily_future_stage_features,
            "ongoing_label": daily_labels[-1] if daily_incomplete else None,
            "ongoing_value": daily_live_duration,
            "ongoing": daily_incomplete,
            "debug_today": today.isoformat(),
            "debug_last_log_date": last_log_date.isoformat(),
            "debug_training_last_label": daily_training_labels[-1] if daily_training_labels else None,
        },
        "daily_efficiency_data": {
            "labels": daily_labels,
            "actuals": daily_efficiencies,
            "trends": _calculate_sma(daily_efficiencies, 7),
            "training_labels": daily_training_labels,
            "training_actuals": daily_training_efficiencies,
            "training_stage_features": daily_training_stage_features,
            "future_stage_features": daily_future_stage_features,
            "ongoing_label": daily_labels[-1] if daily_incomplete else None,
            "ongoing_value": daily_live_efficiency,
            "ongoing": daily_incomplete,
            "debug_today": today.isoformat(),
            "debug_last_log_date": last_log_date.isoformat(),
            "debug_training_last_label": daily_training_labels[-1] if daily_training_labels else None,
        },
    }


def _prepare_stage_annotations(user_id, all_stages, global_start_date, last_log_date):
    """为图表覆盖层准备阶段注释数据"""
    annotations = []
    for stage in all_stages:
        start_g_year, start_g_week = get_custom_week_info(
            stage.start_date, global_start_date
        )

        next_stage_check = (
            Stage.query.filter(
                Stage.user_id == user_id, Stage.start_date > stage.start_date
            )
            .order_by(Stage.start_date.asc())
            .first()
        )

        end_date = (
            (next_stage_check.start_date - timedelta(days=1))
            if next_stage_check
            else last_log_date
        )
        end_g_year, end_g_week = get_custom_week_info(end_date, global_start_date)

        annotations.append(
            {
                "name": stage.name,
                "start_week_label": f"{start_g_year}-W{start_g_week:02}",
                "end_week_label": f"{end_g_year}-W{end_g_week:02}",
            }
        )
    return annotations


def _build_chart_base_payload(user_id: int) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """
    构建统计总览的基础数据，不阻塞在预测计算上。

    返回:
        tuple[payload, forecast_context]
    """
    all_stages = (
        Stage.query.filter_by(user_id=user_id).order_by(Stage.start_date.asc()).all()
    )
    if not all_stages:
        return (
            {
                "kpis": {},
                "stage_annotations": [],
                "setup_needed": True,
                "has_data": False,
                "forecast_status": _build_forecast_status_payload(
                    state="unavailable",
                    signature=None,
                    message="暂无可用于预测的历史数据",
                    updated_at=None,
                    trained_for_date=None,
                ),
            },
            None,
        )

    stage_ids = [s.id for s in all_stages]
    all_logs = LogEntry.query.filter(LogEntry.stage_id.in_(stage_ids)).all()
    if not all_logs:
        return (
            {
                "kpis": {
                    "avg_daily_minutes": 0,
                    "efficiency_star": "N/A",
                    "weekly_trend": "N/A",
                },
                "stage_annotations": [],
                "has_data": False,
                "forecast_status": _build_forecast_status_payload(
                    state="unavailable",
                    signature=None,
                    message="暂无可用于预测的历史数据",
                    updated_at=None,
                    trained_for_date=None,
                ),
            },
            None,
        )

    kpis = _calculate_kpis(user_id, stage_ids)
    trend_data = _prepare_trend_data(user_id, all_stages, all_logs)
    global_start_date = all_stages[0].start_date
    last_log_date = max(log.log_date for log in all_logs)
    stage_annotations = _prepare_stage_annotations(
        user_id, all_stages, global_start_date, last_log_date
    )
    signature = _build_forecast_signature(
        trend_data,
        global_start_date=global_start_date,
        last_log_date=last_log_date,
    )
    base_payload = {
        "kpis": kpis,
        "stage_annotations": stage_annotations,
        "has_data": True,
        "forecast_status": _build_forecast_status_payload(
            state="idle",
            signature=signature,
            message="预测尚未开始",
            updated_at=None,
            trained_for_date=None,
        ),
        **trend_data,
    }
    forecast_context = {
        "signature": signature,
        "global_start_date": global_start_date,
        "last_log_date": last_log_date,
        "forecast_inputs": {
            "daily_labels": trend_data["daily_duration_data"]["training_labels"],
            "daily_duration_values": trend_data["daily_duration_data"]["training_actuals"],
            "daily_efficiency_values": trend_data["daily_efficiency_data"]["training_actuals"],
            "daily_stage_features": trend_data["daily_duration_data"]["training_stage_features"],
            "daily_future_stage_features": trend_data["daily_duration_data"]["future_stage_features"],
            "weekly_labels": trend_data["weekly_duration_data"]["training_labels"],
            "weekly_duration_values": trend_data["weekly_duration_data"]["training_actuals"],
            "weekly_efficiency_values": trend_data["weekly_efficiency_data"]["training_actuals"],
            "weekly_stage_features": trend_data["weekly_duration_data"]["training_stage_features"],
            "weekly_future_stage_features": trend_data["weekly_duration_data"]["future_stage_features"],
            "global_start_date": global_start_date,
            "last_log_date": last_log_date,
            "daily_current_label": trend_data["daily_duration_data"]["ongoing_label"],
            "weekly_current_label": trend_data["weekly_duration_data"]["ongoing_label"],
            "weekly_duration_display_divisor": 7.0,
        },
    }
    return base_payload, forecast_context


def _mark_forecast_bundle_ready(
    forecast_bundle: dict[str, Any],
) -> dict[str, Any]:
    marked_bundle: dict[str, Any] = {}
    for dataset_key in _FORECAST_DATASET_KEYS:
        forecast = copy.deepcopy(
            (forecast_bundle or {}).get(dataset_key) or _build_default_forecast()
        )
        forecast["status"] = "ready" if forecast.get("available") else "unavailable"
        marked_bundle[dataset_key] = forecast
    return marked_bundle


def _store_forecast_entry(
    user_id: int,
    entry: dict[str, Any],
    *,
    instance_path: str | None = None,
    logger: Any | None = None,
    testing: bool = False,
) -> None:
    with _forecast_cache_lock:
        _forecast_cache[user_id] = entry
    if entry.get("state") == "ready":
        _persist_forecast_entry(
            user_id,
            entry,
            instance_path=instance_path,
            logger=logger,
            testing=testing,
        )


def _start_forecast_generation(
    user_id: int,
    *,
    signature: str,
    forecast_inputs: dict[str, Any],
    trained_for_date: str,
    force: bool = False,
) -> None:
    with _forecast_cache_lock:
        cached = _forecast_cache.get(user_id)
        now = time.monotonic()
        if (
            not force
            and cached
            and cached.get("trained_for_date") == trained_for_date
            and cached.get("signature") == signature
            and cached.get("expires_at", 0) > now
            and cached.get("state") in {"pending", "ready"}
        ):
            return

        if (
            cached
            and cached.get("signature") == signature
            and cached.get("expires_at", 0) > now
            and cached.get("state") in {"pending", "ready"}
            and not force
        ):
            return

        wait_event = _forecast_inflight.get(user_id)
        if wait_event is not None and not force:
            return
        if wait_event is not None and force:
            return

        wait_event = threading.Event()
        _forecast_inflight[user_id] = wait_event
        _forecast_cache[user_id] = {
            "signature": signature,
            "state": "pending",
            "message": _PENDING_FORECAST_REASON,
            "updated_at": _utc_now_iso(),
            "trained_for_date": trained_for_date,
            "expires_at": now + _FORECAST_CACHE_TTL_SECONDS,
            "forecast_bundle": _build_pending_forecast_bundle(),
        }

    app = current_app._get_current_object()
    instance_path = app.instance_path
    testing = bool(app.config.get("TESTING"))
    logger = app.logger

    def _runner():
        try:
            forecast_bundle = _mark_forecast_bundle_ready(
                build_trend_forecasts(**forecast_inputs)
            )
            entry = {
                "signature": signature,
                "state": "ready",
                "message": "预测结果已就绪",
                "updated_at": _utc_now_iso(),
                "trained_for_date": trained_for_date,
                "expires_at": time.monotonic() + _FORECAST_CACHE_TTL_SECONDS,
                "forecast_bundle": forecast_bundle,
            }
            _store_forecast_entry(
                user_id,
                entry,
                instance_path=instance_path,
                logger=logger,
                testing=testing,
            )
        except Exception as exc:  # pragma: no cover - defensive logging path
            with app.app_context():
                app.logger.error(
                    "Error generating chart forecasts for user %s: %s",
                    user_id,
                    exc,
                    exc_info=True,
                )
            _store_forecast_entry(
                user_id,
                {
                    "signature": signature,
                    "state": "error",
                    "message": _FORECAST_ERROR_REASON,
                    "updated_at": _utc_now_iso(),
                    "trained_for_date": trained_for_date,
                    "expires_at": time.monotonic() + 30.0,
                    "forecast_bundle": {
                        dataset_key: _build_default_forecast(
                            status="error",
                            reason=_FORECAST_ERROR_REASON,
                        )
                        for dataset_key in _FORECAST_DATASET_KEYS
                    },
                },
                instance_path=instance_path,
                logger=logger,
                testing=testing,
            )
        finally:
            with _forecast_cache_lock:
                event = _forecast_inflight.pop(user_id, None)
                if event is not None:
                    event.set()

    threading.Thread(
        target=_runner,
        name=f"chart-forecast-{user_id}",
        daemon=True,
    ).start()


def _resolve_forecast_entry(
    user_id: int,
    *,
    signature: str,
    forecast_inputs: dict[str, Any],
    force_sync: bool = False,
    force_retrain: bool = False,
) -> dict[str, Any]:
    trained_for_date = _today_cache_key()
    if force_sync or _force_sync_forecast_mode():
        forecast_bundle = _mark_forecast_bundle_ready(
            build_trend_forecasts(**forecast_inputs)
        )
        return {
            "signature": signature,
            "state": "ready",
            "message": "预测结果已就绪",
            "updated_at": _utc_now_iso(),
            "trained_for_date": trained_for_date,
            "forecast_bundle": forecast_bundle,
        }

    now = time.monotonic()
    with _forecast_cache_lock:
        cached = _forecast_cache.get(user_id)
        if (
            cached
            and cached.get("trained_for_date") == trained_for_date
            and cached.get("signature") == signature
            and cached.get("expires_at", 0) > now
            and not force_retrain
        ):
            return copy.deepcopy(cached)

    if not force_retrain:
        persisted = _load_persisted_forecast_entry(user_id)
        if (
            persisted
            and persisted.get("trained_for_date") == trained_for_date
            and persisted.get("signature") == signature
        ):
            persisted["expires_at"] = time.monotonic() + _FORECAST_CACHE_TTL_SECONDS
            _store_forecast_entry(user_id, persisted)
            return copy.deepcopy(persisted)

    _start_forecast_generation(
        user_id,
        signature=signature,
        forecast_inputs=forecast_inputs,
        trained_for_date=trained_for_date,
        force=force_retrain,
    )
    with _forecast_cache_lock:
        cached = _forecast_cache.get(user_id)
        if cached and cached.get("signature") == signature:
            return copy.deepcopy(cached)
    return {
        "signature": signature,
        "state": "pending",
        "message": _PENDING_FORECAST_REASON,
        "updated_at": _utc_now_iso(),
        "trained_for_date": trained_for_date,
        "forecast_bundle": _build_pending_forecast_bundle(),
    }


def _build_chart_data_for_user(
    user_id: int,
    *,
    force_sync_forecasts: bool = False,
) -> dict[str, Any]:
    base_payload, forecast_context = _build_chart_base_payload(user_id)
    if not forecast_context:
        return base_payload

    forecast_entry = _resolve_forecast_entry(
        user_id,
        signature=forecast_context["signature"],
        forecast_inputs=forecast_context["forecast_inputs"],
        force_sync=force_sync_forecasts,
    )
    payload = copy.deepcopy(base_payload)
    _attach_forecast_bundle(payload, forecast_entry.get("forecast_bundle"))
    payload["forecast_status"] = _build_forecast_status_payload(
        state=forecast_entry.get("state", "unavailable"),
        signature=forecast_context["signature"],
        message=forecast_entry.get("message", ""),
        updated_at=forecast_entry.get("updated_at"),
        trained_for_date=forecast_entry.get("trained_for_date"),
    )
    return payload


def get_chart_forecast_status_for_user(user_id: int) -> dict[str, Any]:
    base_payload, forecast_context = _build_chart_base_payload(user_id)
    if not forecast_context:
        return {
            "status": "unavailable",
            "signature": None,
            "message": "暂无可用于预测的历史数据",
            "updated_at": None,
            "trained_for_date": None,
            "forecasts": {
                dataset_key: _build_default_forecast()
                for dataset_key in _FORECAST_DATASET_KEYS
            },
        }

    forecast_entry = _resolve_forecast_entry(
        user_id,
        signature=forecast_context["signature"],
        forecast_inputs=forecast_context["forecast_inputs"],
    )
    return {
        "status": forecast_entry.get("state", "unavailable"),
        "signature": forecast_context["signature"],
        "message": forecast_entry.get("message", ""),
        "updated_at": forecast_entry.get("updated_at"),
        "trained_for_date": forecast_entry.get("trained_for_date"),
        "forecasts": copy.deepcopy(
            forecast_entry.get("forecast_bundle") or _build_pending_forecast_bundle()
        ),
    }


def retrain_chart_forecasts_for_user(user_id: int) -> dict[str, Any]:
    base_payload, forecast_context = _build_chart_base_payload(user_id)
    if not forecast_context:
        return {
            "status": "unavailable",
            "signature": None,
            "message": "暂无可用于预测的历史数据",
            "updated_at": None,
            "trained_for_date": None,
        }

    signature = forecast_context["signature"]
    _clear_persisted_forecast_entry(user_id)
    with _forecast_cache_lock:
        _forecast_cache.pop(user_id, None)

    forecast_entry = _resolve_forecast_entry(
        user_id,
        signature=signature,
        forecast_inputs=forecast_context["forecast_inputs"],
        force_retrain=True,
    )
    return {
        "status": forecast_entry.get("state", "pending"),
        "signature": signature,
        "message": "已开始重新训练预测模型",
        "updated_at": forecast_entry.get("updated_at"),
        "trained_for_date": forecast_entry.get("trained_for_date"),
    }


def get_chart_data_for_user(user_id, *, force_sync_forecasts: bool = False):
    """
    为图表总览提供一个短 TTL 缓存，并对并发请求做去重。

    统计分析页会在短时间内重复请求 overview，且预测计算较重。
    这里让同一用户在 20 秒内复用上一份结果，避免重复训练把请求拖到超时。
    """

    if force_sync_forecasts or _force_sync_forecast_mode():
        return _build_chart_data_for_user(
            user_id,
            force_sync_forecasts=force_sync_forecasts,
        )

    now = time.monotonic()
    wait_event: threading.Event | None = None

    with _overview_cache_lock:
        cached = _overview_cache.get(user_id)
        if cached and cached[0] > now:
            return copy.deepcopy(cached[1])

        wait_event = _overview_inflight.get(user_id)
        if wait_event is None:
            wait_event = threading.Event()
            _overview_inflight[user_id] = wait_event
            is_leader = True
        else:
            is_leader = False

    if not is_leader:
        wait_event.wait(timeout=185)
        with _overview_cache_lock:
            cached = _overview_cache.get(user_id)
            if cached and cached[0] > time.monotonic():
                return copy.deepcopy(cached[1])

    try:
        data = _build_chart_data_for_user(user_id)
        cache_ttl = (
            _OVERVIEW_CACHE_TTL_SECONDS
            if data.get("forecast_status", {}).get("state") == "ready"
            else _PENDING_OVERVIEW_CACHE_TTL_SECONDS
        )
        cache_payload = copy.deepcopy(data)
        with _overview_cache_lock:
            _overview_cache[user_id] = (
                time.monotonic() + cache_ttl,
                cache_payload,
            )
        return data
    finally:
        with _overview_cache_lock:
            event = _overview_inflight.pop(user_id, None)
            if event is not None:
                event.set()


def get_category_chart_data(user_id, stage_id=None, start_date=None, end_date=None):
    """Build category chart dataset for the given user.

    Args:
        user_id: ID of the user requesting the data.
        stage_id: Optional stage ID for filtering results.
        start_date: Optional start date filter (inclusive).
        end_date: Optional end date filter (inclusive).

    Returns:
        dict: Aggregated totals for categories and their subcategories.
    """
    # 首先尝试使用新的分类系统（Category + SubCategory）
    query = (
        db.session.query(
            Category.name, SubCategory.name, func.sum(LogEntry.actual_duration)
        )
        .join(SubCategory, LogEntry.subcategory_id == SubCategory.id)
        .join(Category, SubCategory.category_id == Category.id)
        .filter(Category.user_id == user_id)
        .group_by(Category.name, SubCategory.name)
    )

    if stage_id:
        query = query.filter(LogEntry.stage_id == stage_id)

    if start_date:
        query = query.filter(LogEntry.log_date >= start_date)

    if end_date:
        query = query.filter(LogEntry.log_date <= end_date)

    results = query.all()

    # 如果新分类系统没有数据，回退到 legacy_category
    if not results:
        # 尝试使用 legacy_category
        legacy_query = (
            db.session.query(
                LogEntry.legacy_category, func.sum(LogEntry.actual_duration)
            )
            .join(Stage, LogEntry.stage_id == Stage.id)
            .filter(
                Stage.user_id == user_id,
                LogEntry.legacy_category.isnot(None),
                LogEntry.legacy_category != "",
            )
            .group_by(LogEntry.legacy_category)
        )

        if stage_id:
            legacy_query = legacy_query.filter(LogEntry.stage_id == stage_id)

        if start_date:
            legacy_query = legacy_query.filter(LogEntry.log_date >= start_date)

        if end_date:
            legacy_query = legacy_query.filter(LogEntry.log_date <= end_date)

        legacy_results = legacy_query.all()

        if not legacy_results:
            return None

        # 构建基于 legacy_category 的数据结构
        legacy_category_data: dict[str, float] = {}
        for legacy_cat, duration in legacy_results:
            duration_hours = (duration or 0) / 60.0
            legacy_category_data[legacy_cat] = duration_hours

        legacy_sorted_categories = sorted(
            legacy_category_data.items(), key=lambda item: item[1], reverse=True
        )

        main_labels = [item[0] for item in legacy_sorted_categories]
        main_data = [round(item[1], 2) for item in legacy_sorted_categories]

        # legacy_category 没有子分类，drilldown 为空字典
        return {"main": {"labels": main_labels, "data": main_data}, "drilldown": {}}

    category_data: dict[str, _CategoryAgg] = {}
    for cat_name, sub_name, duration in results:
        duration_hours = (duration or 0) / 60.0
        if cat_name is None:
            continue
        entry = category_data.setdefault(cat_name, {"total": 0.0, "subs": []})
        entry["total"] += duration_hours
        entry["subs"].append(
            {
                "name": str(sub_name) if sub_name is not None else "",
                "duration": round(duration_hours, 2),
            }
        )

    sorted_categories: list[tuple[str, _CategoryAgg]] = sorted(
        category_data.items(), key=lambda item: item[1]["total"], reverse=True
    )

    main_labels = [item[0] for item in sorted_categories]
    main_data = [round(item[1]["total"], 2) for item in sorted_categories]
    sub_data = {
        cat_name: {
            "labels": [
                sub["name"]
                for sub in sorted(
                    cat_info["subs"], key=lambda x: x["duration"], reverse=True
                )
            ],
            "data": [
                sub["duration"]
                for sub in sorted(
                    cat_info["subs"], key=lambda x: x["duration"], reverse=True
                )
            ],
        }
        for cat_name, cat_info in sorted_categories
    }

    return {"main": {"labels": main_labels, "data": main_data}, "drilldown": sub_data}


def _iter_days(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())  # Monday=0


def get_category_trend_series(
    user_id: int,
    *,
    category_id: int | None = None,
    subcategory_id: int | None = None,
    stage_id: int | None = None,
    range_mode: str = "all",
    start_date: date | None = None,
    end_date: date | None = None,
    granularity: str | None = None,
):
    """Return aggregated hours series for a category/subcategory."""

    range_mode = (range_mode or "all").lower()

    base = (
        db.session.query(LogEntry.log_date, func.sum(LogEntry.actual_duration))
        .join(Stage, LogEntry.stage_id == Stage.id)
        .filter(Stage.user_id == user_id)
    )

    if subcategory_id:
        base = base.filter(LogEntry.subcategory_id == subcategory_id)
    elif category_id:
        base = base.join(SubCategory, LogEntry.subcategory_id == SubCategory.id)
        base = base.filter(SubCategory.category_id == category_id)

    if stage_id:
        base = base.filter(LogEntry.stage_id == stage_id)

    # 处理默认时间范围
    today = date.today()

    if start_date is None or end_date is None:
        if range_mode == "stage" and stage_id:
            stage = Stage.query.filter_by(id=stage_id, user_id=user_id).first()
            if stage:
                start_date = start_date or stage.start_date
                last_log = (
                    db.session.query(func.max(LogEntry.log_date))
                    .filter(LogEntry.stage_id == stage.id)
                    .scalar()
                )
                end_date = end_date or last_log or today
        elif range_mode == "all":
            min_date = base.with_entities(func.min(LogEntry.log_date)).scalar()
            max_date = base.with_entities(func.max(LogEntry.log_date)).scalar()
            start_date = start_date or min_date or today
            end_date = end_date or max_date or today

    # 若仍缺少，则使用默认窗口
    if end_date is None:
        end_date = today
    if start_date is None:
        start_date = end_date - timedelta(weeks=11)

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    query = base.filter(
        LogEntry.log_date >= start_date,
        LogEntry.log_date <= end_date,
    )

    rows = query.group_by(LogEntry.log_date).order_by(LogEntry.log_date.asc()).all()

    used_legacy_name: str | None = None

    # 如果没有新体系数据且给定分类，尝试 legacy_category
    # 说明：很多历史数据只记录了 legacy_category（没有子分类），
    # 当前端选择了子分类但新体系下没有对应数据时，这里也回退到按分类聚合的 legacy 数据，
    # 以免“分类趋势”长期为空。
    if not rows and category_id:
        category = Category.query.filter_by(id=category_id, user_id=user_id).first()
        if category and category.name:
            used_legacy_name = category.name
            legacy_query = (
                db.session.query(LogEntry.log_date, func.sum(LogEntry.actual_duration))
                .join(Stage, LogEntry.stage_id == Stage.id)
                .filter(
                    Stage.user_id == user_id,
                    LogEntry.legacy_category == category.name,
                    LogEntry.log_date >= start_date,
                    LogEntry.log_date <= end_date,
                )
            )
            if stage_id:
                legacy_query = legacy_query.filter(LogEntry.stage_id == stage_id)
            rows = (
                legacy_query.group_by(LogEntry.log_date)
                .order_by(LogEntry.log_date.asc())
                .all()
            )

    # 若没有任何记录，也需要按所选区间返回完整的日序列（全为 0）
    # 这样前端能明确看到区间而不是空白提示
    if not rows:
        days = list(_iter_days(start_date, end_date))
        zero_daily = [0.0 for _ in days]
        # 粒度策略与后续一致：若强制按日，则直接返回日序列
        gran_override = (granularity or "").lower() if granularity else None
        if gran_override == "daily":
            return {
                "labels": [day.isoformat() for day in days],
                "data": zero_daily,
                "granularity": "daily",
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            }
        # 否则仍按周聚合（结果也为 0）
        zero_week_map: dict[date, float] = {}
        for day in days:
            start_of_week = _week_start(day)
            zero_week_map[start_of_week] = round(
                zero_week_map.get(start_of_week, 0) + 0, 2
            )
        weeks = sorted(zero_week_map.keys()) or [_week_start(start_date)]
        return {
            "labels": [week.isoformat() for week in weeks],
            "data": [zero_week_map.get(week, 0) for week in weeks],
            "granularity": "weekly",
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        }

    day_map = {log_date: int(duration or 0) for log_date, duration in rows}
    days = list(_iter_days(start_date, end_date))

    daily_hours = [round(day_map.get(day, 0) / 60.0, 2) for day in days]

    delta_days = (end_date - start_date).days + 1
    # 支持外部强制粒度
    gran_override = (granularity or "").lower()
    if gran_override in ("daily", "weekly"):
        selected_granularity = gran_override
    else:
        # 小于等于 35 天走日粒度；明确选择“按日”也走日粒度；否则按周
        selected_granularity = (
            "daily" if (delta_days <= 35 or range_mode == "daily") else "weekly"
        )

    if selected_granularity == "daily":
        return {
            "labels": [day.isoformat() for day in days],
            "data": daily_hours,
            "granularity": "daily",
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            **({"legacy_name": used_legacy_name} if used_legacy_name else {}),
        }

    # 聚合为周数据（周一为起点）
    week_map: dict[date, float] = {}
    for day, hours in zip(days, daily_hours):
        start_of_week = _week_start(day)
        week_map[start_of_week] = round(week_map.get(start_of_week, 0) + hours, 2)

    weeks = sorted(week_map.keys())
    return {
        "labels": [week.isoformat() for week in weeks],
        "data": [week_map[week] for week in weeks],
        "granularity": "weekly",
        "start": start_date.isoformat(),
        "end": end_date.isoformat(),
        **({"legacy_name": used_legacy_name} if used_legacy_name else {}),
    }


def get_category_efficiency_chart_data(
    user_id, stage_id=None, start_date=None, end_date=None
):
    """
    计算分类效率占比数据
    效率算法：日·分类效率 = avg_mood_cat * log(1 + hours_cat)
    """
    # 新分类系统查询
    query = (
        db.session.query(
            Category.name,
            SubCategory.name,
            LogEntry.log_date,
            func.sum(LogEntry.actual_duration).label("total_duration"),
            func.sum(LogEntry.actual_duration * func.coalesce(LogEntry.mood, 3)).label(
                "weighted_mood"
            ),
        )
        .join(SubCategory, LogEntry.subcategory_id == SubCategory.id)
        .join(Category, SubCategory.category_id == Category.id)
        .filter(Category.user_id == user_id)
        .group_by(Category.name, SubCategory.name, LogEntry.log_date)
    )

    if stage_id:
        query = query.filter(LogEntry.stage_id == stage_id)
    if start_date:
        query = query.filter(LogEntry.log_date >= start_date)
    if end_date:
        query = query.filter(LogEntry.log_date <= end_date)

    results = query.all()

    if not results:
        # 回退到 legacy_category
        legacy_query = (
            db.session.query(
                LogEntry.legacy_category,
                LogEntry.log_date,
                func.sum(LogEntry.actual_duration).label("total_duration"),
                func.sum(
                    LogEntry.actual_duration * func.coalesce(LogEntry.mood, 3)
                ).label("weighted_mood"),
            )
            .join(Stage, LogEntry.stage_id == Stage.id)
            .filter(
                Stage.user_id == user_id,
                LogEntry.legacy_category.isnot(None),
                LogEntry.legacy_category != "",
            )
            .group_by(LogEntry.legacy_category, LogEntry.log_date)
        )

        if stage_id:
            legacy_query = legacy_query.filter(LogEntry.stage_id == stage_id)
        if start_date:
            legacy_query = legacy_query.filter(LogEntry.log_date >= start_date)
        if end_date:
            legacy_query = legacy_query.filter(LogEntry.log_date <= end_date)

        legacy_results = legacy_query.all()

        if not legacy_results:
            return None

        # 计算每日效率，然后汇总到类别
        legacy_efficiency_map: dict[str, float] = {}
        for legacy_cat, log_date, duration, weighted_mood in legacy_results:
            hours = (duration or 0) / 60.0
            avg_mood = (weighted_mood or 0) / (duration or 1)  # 避免除0
            daily_efficiency = avg_mood * math.log(1 + hours)

            if legacy_cat not in legacy_efficiency_map:
                legacy_efficiency_map[legacy_cat] = 0.0
            legacy_efficiency_map[legacy_cat] += daily_efficiency

        legacy_sorted_categories = sorted(
            legacy_efficiency_map.items(), key=lambda item: item[1], reverse=True
        )

        main_labels = [item[0] for item in legacy_sorted_categories]
        main_data = [round(item[1], 2) for item in legacy_sorted_categories]

        return {"main": {"labels": main_labels, "data": main_data}, "drilldown": {}}

    # 新分类系统：计算效率
    # 首先按分类、子分类、日期分组计算每日效率
    category_efficiency: dict[str, _CategoryAgg] = {}

    for cat_name, sub_name, log_date, duration, weighted_mood in results:
        if cat_name is None:
            continue

        hours = (duration or 0) / 60.0
        avg_mood = (weighted_mood or 0) / (duration or 1)
        daily_efficiency = avg_mood * math.log(1 + hours)

        entry = category_efficiency.setdefault(cat_name, {"total": 0.0, "subs": []})
        entry["total"] += daily_efficiency

        # 查找或创建子分类条目
        sub_name_str = str(sub_name) if sub_name is not None else ""
        sub_entry = next(
            (s for s in entry["subs"] if s.get("name") == sub_name_str), None
        )
        if sub_entry is None:
            sub_entry = {"name": sub_name_str, "duration": 0.0}
            entry["subs"].append(sub_entry)
        sub_entry["duration"] += daily_efficiency

    sorted_categories: list[tuple[str, _CategoryAgg]] = sorted(
        category_efficiency.items(), key=lambda item: item[1]["total"], reverse=True
    )

    main_labels = [item[0] for item in sorted_categories]
    main_data = [round(item[1]["total"], 2) for item in sorted_categories]

    sub_data = {
        cat_name: {
            "labels": [
                sub["name"]
                for sub in sorted(
                    cat_info["subs"], key=lambda x: x["duration"], reverse=True
                )
            ],
            "data": [
                round(sub["duration"], 2)
                for sub in sorted(
                    cat_info["subs"], key=lambda x: x["duration"], reverse=True
                )
            ],
        }
        for cat_name, cat_info in sorted_categories
    }

    return {"main": {"labels": main_labels, "data": main_data}, "drilldown": sub_data}


def get_category_efficiency_trend_series(
    user_id: int,
    *,
    category_id: int | None = None,
    subcategory_id: int | None = None,
    stage_id: int | None = None,
    range_mode: str = "all",
    start_date: date | None = None,
    end_date: date | None = None,
    granularity: str | None = None,
):
    """
    返回按分类的效率趋势序列
    效率算法：日·分类效率 = avg_mood_cat * log(1 + hours_cat)
    """
    range_mode = (range_mode or "all").lower()

    # 查询基础数据：日期、时长、加权心情
    base = (
        db.session.query(
            LogEntry.log_date,
            func.sum(LogEntry.actual_duration).label("total_duration"),
            func.sum(LogEntry.actual_duration * func.coalesce(LogEntry.mood, 3)).label(
                "weighted_mood"
            ),
        )
        .join(Stage, LogEntry.stage_id == Stage.id)
        .filter(Stage.user_id == user_id)
    )

    if subcategory_id:
        base = base.filter(LogEntry.subcategory_id == subcategory_id)
    elif category_id:
        base = base.join(SubCategory, LogEntry.subcategory_id == SubCategory.id)
        base = base.filter(SubCategory.category_id == category_id)

    if stage_id:
        base = base.filter(LogEntry.stage_id == stage_id)

    # 处理默认时间范围
    today = date.today()

    if start_date is None or end_date is None:
        if range_mode == "stage" and stage_id:
            stage = Stage.query.filter_by(id=stage_id, user_id=user_id).first()
            if stage:
                start_date = start_date or stage.start_date
                last_log = (
                    db.session.query(func.max(LogEntry.log_date))
                    .filter(LogEntry.stage_id == stage.id)
                    .scalar()
                )
                end_date = end_date or last_log or today
        elif range_mode == "all":
            min_date = base.with_entities(func.min(LogEntry.log_date)).scalar()
            max_date = base.with_entities(func.max(LogEntry.log_date)).scalar()
            start_date = start_date or min_date or today
            end_date = end_date or max_date or today

    if end_date is None:
        end_date = today
    if start_date is None:
        start_date = end_date - timedelta(weeks=11)

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    query = base.filter(
        LogEntry.log_date >= start_date,
        LogEntry.log_date <= end_date,
    ).group_by(LogEntry.log_date)

    rows = query.all()

    if not rows:
        delta_days = (end_date - start_date).days + 1
        gran_override = (granularity or "").lower()
        if gran_override in ("daily", "weekly"):
            selected_granularity = gran_override
        else:
            selected_granularity = (
                "daily" if (delta_days <= 35 or range_mode == "daily") else "weekly"
            )

        days = list(_iter_days(start_date, end_date))
        if selected_granularity == "daily":
            return {
                "labels": [day.isoformat() for day in days],
                "data": [0] * len(days),
                "granularity": "daily",
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            }

        # 按周聚合
        zero_week_map: dict[date, float] = {}
        for day in days:
            start_of_week = _week_start(day)
            zero_week_map[start_of_week] = 0
        weeks = sorted(zero_week_map.keys()) or [_week_start(start_date)]
        return {
            "labels": [week.isoformat() for week in weeks],
            "data": [0] * len(weeks),
            "granularity": "weekly",
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        }

    # 计算每日效率
    day_efficiency_map = {}
    for log_date, duration, weighted_mood in rows:
        hours = (duration or 0) / 60.0
        avg_mood = (weighted_mood or 0) / (duration or 1)
        daily_efficiency = avg_mood * math.log(1 + hours)
        day_efficiency_map[log_date] = daily_efficiency

    days = list(_iter_days(start_date, end_date))
    daily_efficiencies = [round(day_efficiency_map.get(day, 0), 2) for day in days]

    delta_days = (end_date - start_date).days + 1
    gran_override = (granularity or "").lower()
    if gran_override in ("daily", "weekly"):
        selected_granularity = gran_override
    else:
        selected_granularity = (
            "daily" if (delta_days <= 35 or range_mode == "daily") else "weekly"
        )

    if selected_granularity == "daily":
        return {
            "labels": [day.isoformat() for day in days],
            "data": daily_efficiencies,
            "granularity": "daily",
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        }

    # 聚合为周数据（周一为起点）
    week_map: dict[date, float] = {}
    for day, efficiency in zip(days, daily_efficiencies):
        start_of_week = _week_start(day)
        week_map[start_of_week] = round(week_map.get(start_of_week, 0) + efficiency, 2)

    weeks = sorted(week_map.keys())
    return {
        "labels": [week.isoformat() for week in weeks],
        "data": [week_map[week] for week in weeks],
        "granularity": "weekly",
        "start": start_date.isoformat(),
        "end": end_date.isoformat(),
    }
