from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional, Tuple

from app.models import LogEntry, Stage

from .errors import AIPlannerError


SCOPE_LABELS = {
    "day": "日度",
    "week": "周度",
    "month": "月度",
    "stage": "阶段",
}


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise AIPlannerError("日期格式应为 YYYY-MM-DD") from exc


def _get_date_range_for_scope(
    scope: str,
    date_str: Optional[str],
    stage_id: Optional[int],
    user_id: int,
) -> Tuple[Optional[date], Optional[date], Optional[Stage]]:
    """
    Resolve the analysis window based on scope and parameters.
    """
    scope = scope.lower()
    if scope not in SCOPE_LABELS:
        raise AIPlannerError("暂不支持的分析范围")

    if scope == "stage":
        if not stage_id:
            raise AIPlannerError("请选择要分析的阶段")
        stage = Stage.query.filter_by(id=stage_id, user_id=user_id).first()
        if not stage:
            raise AIPlannerError("阶段不存在或无权访问")
        start = stage.start_date
        # determine end date as last log for stage or today whichever later
        last_log = (
            LogEntry.query.filter_by(stage_id=stage.id)
            .order_by(LogEntry.log_date.desc())
            .first()
        )
        end = last_log.log_date if last_log else date.today()
        return start, end, stage

    if not date_str:
        target_date = date.today()
    else:
        target_date = _parse_date(date_str)

    if scope == "day":
        return target_date, target_date, None
    if scope == "week":
        # 将传入日期视为该周任意一天，周一为开始
        weekday = target_date.weekday()  # Monday=0
        start = target_date - timedelta(days=weekday)
        end = start + timedelta(days=6)
        return start, end, None
    if scope == "month":
        start = target_date.replace(day=1)
        # next month
        if start.month == 12:
            next_month = start.replace(year=start.year + 1, month=1, day=1)
        else:
            next_month = start.replace(month=start.month + 1, day=1)
        end = next_month - timedelta(days=1)
        return start, end, None

    raise AIPlannerError("不支持的分析范围")


def _get_next_range(
    scope: str,
    start: Optional[date],
    end: Optional[date],
    stage: Optional[Stage],
    user_id: int,
) -> Tuple[Optional[date], Optional[date], Optional[str]]:
    """
    Determine the next planning window based on scope.
    Returns start, end, and optional label (e.g. 下一阶段名称)
    """
    scope = scope.lower()
    if scope == "day":
        if not end:
            return None, None, None
        next_day = end + timedelta(days=1)
        return next_day, next_day, None
    if scope == "week":
        if not end:
            return None, None, None
        next_start = end + timedelta(days=1)
        next_end = next_start + timedelta(days=6)
        return next_start, next_end, None
    if scope == "month":
        if not start:
            return None, None, None
        if start.month == 12:
            next_start = start.replace(year=start.year + 1, month=1, day=1)
        else:
            next_start = start.replace(month=start.month + 1, day=1)
        if next_start.month == 12:
            next_next = next_start.replace(year=next_start.year + 1, month=1, day=1)
        else:
            next_next = next_start.replace(month=next_start.month + 1, day=1)
        next_end = next_next - timedelta(days=1)
        return next_start, next_end, None
    if scope == "stage":
        if not stage:
            return None, None, None
        next_stage = (
            Stage.query.filter(
                Stage.user_id == user_id, Stage.start_date > stage.start_date
            )
            .order_by(Stage.start_date.asc())
            .first()
        )
        if next_stage:
            next_last_log = (
                LogEntry.query.filter_by(stage_id=next_stage.id)
                .order_by(LogEntry.log_date.desc())
                .first()
            )
            if next_last_log and next_last_log.log_date:
                next_end = next_last_log.log_date
            else:
                next_end = max(date.today(), next_stage.start_date)
            return next_stage.start_date, next_end, next_stage.name
        # fallback: plan for two weeks after current stage ends
        if end:
            fallback_start = end + timedelta(days=1)
            fallback_end = fallback_start + timedelta(days=13)
            return fallback_start, fallback_end, None
    return None, None, None


def _get_prev_range(
    scope: str,
    start: Optional[date],
    end: Optional[date],
) -> Tuple[Optional[date], Optional[date]]:
    """Return the previous window relative to [start, end] for day/week/month.
    Stage 级别不提供上一阶段（因无法可靠推断）。
    """
    scope = scope.lower()
    if not start or not end:
        return None, None
    if scope == "day":
        prev = start - timedelta(days=1)
        return prev, prev
    if scope == "week":
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=6)
        return prev_start, prev_end
    if scope == "month":
        prev_end = start - timedelta(days=1)
        prev_start = prev_end.replace(day=1)
        return prev_start, prev_end
    return None, None


def _format_period_label(scope: str, start: Optional[date], end: Optional[date]) -> str:
    scope_label = SCOPE_LABELS.get(scope, scope)
    if start and end:
        if start == end:
            return f"{scope_label}（{start.isoformat()}）"
        return f"{scope_label}（{start.isoformat()} 至 {end.isoformat()}）"
    return scope_label


__all__ = [
    "SCOPE_LABELS",
    "_parse_date",
    "_get_date_range_for_scope",
    "_get_next_range",
    "_get_prev_range",
    "_format_period_label",
]
