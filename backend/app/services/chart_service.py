"""
图表统计服务
"""

import collections
import math
from datetime import date, timedelta
from typing import Sequence, TypedDict
from sqlalchemy import func, desc
import numpy as np

from app import db
from app.models import Stage, LogEntry, WeeklyData, DailyData, Category, SubCategory
from .helpers import get_custom_week_info


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


def _prepare_trend_data(user_id, all_stages, all_logs):
    """准备每日和每周趋势的数据结构"""
    first_log_date = min(log.log_date for log in all_logs)
    last_log_date = date.today()
    global_start_date = all_stages[0].start_date
    stage_ids = [s.id for s in all_stages]

    date_range = [
        first_log_date + timedelta(days=x)
        for x in range((last_log_date - first_log_date).days + 1)
    ]
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
    daily_efficiencies = [daily_efficiency_map.get(d) for d in date_range]

    weekly_data: dict[tuple[int, int], _WeekBucket] = collections.defaultdict(
        lambda: {"duration": 0.0, "efficiency": None, "days": 0}
    )
    for d in date_range:
        year, week_num = get_custom_week_info(d, global_start_date)
        weekly_data[(year, week_num)]["duration"] += float(
            daily_duration_map.get(d) or 0
        )
        weekly_data[(year, week_num)]["days"] += 1

    weekly_efficiency_from_db = (
        WeeklyData.query.join(Stage).filter(Stage.user_id == user_id).all()
    )
    for w_eff in weekly_efficiency_from_db:
        week_start_in_stage = w_eff.stage.start_date + timedelta(
            weeks=w_eff.week_num - 1
        )
        global_year, global_week_num = get_custom_week_info(
            week_start_in_stage, global_start_date
        )
        if (global_year, global_week_num) in weekly_data:
            weekly_data[(global_year, global_week_num)]["efficiency"] = w_eff.efficiency

    sorted_week_keys = sorted(weekly_data.keys())
    weekly_labels = [f"{k[0]}-W{k[1]:02}" for k in sorted_week_keys]
    # 计算周平均时长：总时长除以该周包含的天数
    weekly_durations = []
    for k in sorted_week_keys:
        duration = weekly_data[k]["duration"]
        days = weekly_data[k]["days"] or 0
        weekly_durations.append(round(duration / 60 / max(days, 1), 2))
    weekly_efficiencies = [weekly_data[k]["efficiency"] for k in sorted_week_keys]

    return {
        "weekly_duration_data": {
            "labels": weekly_labels,
            "actuals": weekly_durations,
            "trends": _calculate_sma(weekly_durations, 3),
        },
        "weekly_efficiency_data": {
            "labels": weekly_labels,
            "actuals": weekly_efficiencies,
            "trends": _calculate_sma(weekly_efficiencies, 3),
        },
        "daily_duration_data": {
            "labels": daily_labels,
            "actuals": daily_durations,
            "trends": _calculate_sma(daily_durations, 7),
        },
        "daily_efficiency_data": {
            "labels": daily_labels,
            "actuals": daily_efficiencies,
            "trends": _calculate_sma(daily_efficiencies, 7),
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


def get_chart_data_for_user(user_id):
    """
    为前端渲染图表准备所有必要的数据

    返回:
        dict: 包含KPIs、趋势数据、阶段注释等的字典
    """
    all_stages = (
        Stage.query.filter_by(user_id=user_id).order_by(Stage.start_date.asc()).all()
    )
    if not all_stages:
        return {
            "kpis": {},
            "stage_annotations": [],
            "setup_needed": True,
            "has_data": False,
        }

    stage_ids = [s.id for s in all_stages]
    all_logs = LogEntry.query.filter(LogEntry.stage_id.in_(stage_ids)).all()
    if not all_logs:
        return {
            "kpis": {
                "avg_daily_minutes": 0,
                "efficiency_star": "N/A",
                "weekly_trend": "N/A",
            },
            "has_data": False,
        }

    kpis = _calculate_kpis(user_id, stage_ids)
    trend_data = _prepare_trend_data(user_id, all_stages, all_logs)

    global_start_date = all_stages[0].start_date
    last_log_date = date.today()
    stage_annotations = _prepare_stage_annotations(
        user_id, all_stages, global_start_date, last_log_date
    )

    final_data = {
        "kpis": kpis,
        "stage_annotations": stage_annotations,
        "has_data": True,
        **trend_data,
    }

    return final_data


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
