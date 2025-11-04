"""
Leaderboard service
Handles cross-user rankings and public statistics for shared data.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple, Optional

from sqlalchemy import func, desc

from app import db
from app.models import User, Stage, LogEntry, DailyData, Setting
from app.services.chart_service import get_category_chart_data

_OPT_IN_KEY = "leaderboard_opt_in"
_ALLOWED_PERIODS = {"day", "week", "month"}
_ALLOWED_METRICS = {"duration", "efficiency"}


def _current_period_range(period: str) -> Tuple[date, date]:
    today = date.today()
    if period == "day":
        return today, today
    if period == "week":
        start = today - timedelta(days=6)
        end = today
        return start, end
    if period == "month":
        start = today - timedelta(days=29)
        end = today
        return start, end
    raise ValueError(f"Unsupported period: {period}")


def is_user_opted_in(user_id: int) -> bool:
    setting = Setting.query.filter_by(user_id=user_id, key=_OPT_IN_KEY).first()
    if not setting:
        return False
    return setting.value.lower() == "true"


def set_leaderboard_opt_in(user_id: int, opt_in: bool) -> None:
    setting = Setting.query.filter_by(user_id=user_id, key=_OPT_IN_KEY).first()
    value = "true" if opt_in else "false"
    if not setting:
        if not opt_in:
            # Nothing to do if record absent and user opts out.
            return
        setting = Setting(key=_OPT_IN_KEY, value=value, user_id=user_id)
        db.session.add(setting)
    else:
        setting.value = value
        db.session.add(setting)
    db.session.commit()


def _build_rank_record(
    user_id: int,
    username: str,
    total_duration: Optional[float],
    avg_efficiency: Optional[float],
    sessions: Optional[int],
    last_activity: Optional[date],
    rank: int,
) -> Dict[str, object]:
    duration_minutes = int(total_duration or 0)
    avg_eff = None
    if avg_efficiency is not None:
        avg_eff = round(float(avg_efficiency), 2)
    return {
        "user_id": user_id,
        "username": username,
        "total_duration_minutes": duration_minutes,
        "total_duration_hours": round(duration_minutes / 60, 2) if duration_minutes else 0.0,
        "average_efficiency": avg_eff,
        "sessions": int(sessions or 0),
        "last_activity": last_activity.isoformat() if last_activity else None,
        "rank": rank,
    }


def get_leaderboard_rankings(
    requesting_user_id: int,
    period: str = "week",
    metric: str = "duration",
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, object]:
    if period not in _ALLOWED_PERIODS:
        raise ValueError("Invalid period parameter")
    if metric not in _ALLOWED_METRICS:
        raise ValueError("Invalid metric parameter")

    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    start_date, end_date = _current_period_range(period)

    opted_in_subquery = (
        db.session.query(Setting.user_id)
        .filter(Setting.key == _OPT_IN_KEY, Setting.value == "true")
        .subquery()
    )

    duration_subquery = (
        db.session.query(
            Stage.user_id.label("user_id"),
            func.coalesce(func.sum(LogEntry.actual_duration), 0).label("total_duration"),
            func.count(LogEntry.id).label("sessions"),
            func.max(LogEntry.log_date).label("last_activity"),
        )
        .join(LogEntry, Stage.id == LogEntry.stage_id)
        .filter(LogEntry.log_date >= start_date, LogEntry.log_date <= end_date)
        .group_by(Stage.user_id)
        .subquery()
    )

    efficiency_subquery = (
        db.session.query(
            Stage.user_id.label("user_id"),
            func.avg(DailyData.efficiency).label("avg_efficiency"),
        )
        .join(DailyData, Stage.id == DailyData.stage_id)
        .filter(
            DailyData.log_date >= start_date,
            DailyData.log_date <= end_date,
            DailyData.efficiency.isnot(None),
        )
        .group_by(Stage.user_id)
        .subquery()
    )

    base_query = (
        db.session.query(
            User.id.label("user_id"),
            User.username,
            duration_subquery.c.total_duration,
            efficiency_subquery.c.avg_efficiency,
            duration_subquery.c.sessions,
            duration_subquery.c.last_activity,
        )
        .join(opted_in_subquery, opted_in_subquery.c.user_id == User.id)
        .outerjoin(duration_subquery, duration_subquery.c.user_id == User.id)
        .outerjoin(efficiency_subquery, efficiency_subquery.c.user_id == User.id)
    )

    order_clauses = []
    if metric == "duration":
        order_clauses.append(desc(func.coalesce(duration_subquery.c.total_duration, 0)))
        order_clauses.append(desc(func.coalesce(efficiency_subquery.c.avg_efficiency, 0)))
    else:
        order_clauses.append(desc(func.coalesce(efficiency_subquery.c.avg_efficiency, 0)))
        order_clauses.append(desc(func.coalesce(duration_subquery.c.total_duration, 0)))
    order_clauses.append(User.username.asc())

    rows = base_query.order_by(*order_clauses).all()
    total = len(rows)

    ranking_records: List[Dict[str, object]] = []
    for position, row in enumerate(rows, start=1):
        record = _build_rank_record(
            row.user_id,
            row.username,
            row.total_duration,
            row.avg_efficiency,
            row.sessions,
            row.last_activity,
            position,
        )
        ranking_records.append(record)

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paged_items = ranking_records[start_idx:end_idx]

    me_record = next(
        (record for record in ranking_records if record["user_id"] == requesting_user_id),
        None,
    )

    return {
        "success": True,
        "data": {
            "period": period,
            "metric": metric,
            "range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": paged_items,
            "me": me_record,
            "opted_in": is_user_opted_in(requesting_user_id),
        },
    }


def get_user_public_stats(target_user_id: int, period: str) -> Optional[Dict[str, object]]:
    if period not in _ALLOWED_PERIODS:
        raise ValueError("Invalid period parameter")

    user = User.query.get(target_user_id)
    if not user or not is_user_opted_in(target_user_id):
        return None

    start_date, end_date = _current_period_range(period)

    duration_rows = (
        db.session.query(
            LogEntry.log_date.label("log_date"),
            func.coalesce(func.sum(LogEntry.actual_duration), 0).label("total_duration"),
            func.count(LogEntry.id).label("sessions"),
        )
        .join(Stage, Stage.id == LogEntry.stage_id)
        .filter(
            Stage.user_id == target_user_id,
            LogEntry.log_date >= start_date,
            LogEntry.log_date <= end_date,
        )
        .group_by(LogEntry.log_date)
        .order_by(LogEntry.log_date)
        .all()
    )

    efficiency_rows = (
        db.session.query(
            DailyData.log_date.label("log_date"),
            func.avg(DailyData.efficiency).label("avg_efficiency"),
        )
        .join(Stage, Stage.id == DailyData.stage_id)
        .filter(
            Stage.user_id == target_user_id,
            DailyData.log_date >= start_date,
            DailyData.log_date <= end_date,
            DailyData.efficiency.isnot(None),
        )
        .group_by(DailyData.log_date)
        .all()
    )

    duration_map = {
        row.log_date: {
            "duration": int(row.total_duration or 0),
            "sessions": int(row.sessions or 0),
        }
        for row in duration_rows
    }
    efficiency_map = {
        row.log_date: float(row.avg_efficiency)
        for row in efficiency_rows
        if row.avg_efficiency is not None
    }

    combined_dates = sorted(set(duration_map.keys()) | set(efficiency_map.keys()))

    daily_trend = []
    for entry_date in combined_dates:
        duration_info = duration_map.get(entry_date, {})
        efficiency_value = efficiency_map.get(entry_date)
        trend_item = {
            "date": entry_date.isoformat(),
            "duration_minutes": duration_info.get("duration", 0),
            "sessions": duration_info.get("sessions", 0),
            "average_efficiency": round(float(efficiency_value), 2)
            if efficiency_value is not None
            else None,
        }
        daily_trend.append(trend_item)

    total_duration = sum(item["duration"] for item in duration_map.values())
    total_sessions = sum(item["sessions"] for item in duration_map.values())
    average_efficiency = None
    if efficiency_map:
        average_efficiency = round(
            sum(efficiency_map.values()) / len(efficiency_map), 2
        )

    last_activity_date = None
    if duration_map:
        last_activity_date = max(duration_map.keys()).isoformat()

    category_breakdown = get_category_chart_data(
        target_user_id, start_date=start_date, end_date=end_date
    )

    return {
        "success": True,
        "data": {
            "user": {
                "id": user.id,
                "username": user.username,
            },
            "period": period,
            "range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "summary": {
                "total_duration_minutes": total_duration,
                "total_duration_hours": round(total_duration / 60, 2)
                if total_duration
                else 0.0,
                "average_efficiency": average_efficiency,
                "sessions": total_sessions,
                "days_active": len(duration_map),
                "last_activity": last_activity_date,
            },
            "daily_trend": daily_trend,
            "categories": category_breakdown or {"main": {"labels": [], "data": []}, "drilldown": {}},
        },
    }
