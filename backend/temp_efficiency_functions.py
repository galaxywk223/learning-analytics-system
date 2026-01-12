# 临时文件：效率计算函数
# 这些函数将添加到 chart_service.py

import math
from datetime import date, timedelta
from typing import TypedDict
from sqlalchemy import func
from app import db
from app.models import LogEntry, Stage, Category, SubCategory


class _CategorySub(TypedDict):
    name: str
    efficiency: float


class _CategoryEfficiency(TypedDict):
    total: float
    subs: list[_CategorySub]


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
    category_efficiency: dict[str, _CategoryEfficiency] = {}

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
        sub_entry = next((s for s in entry["subs"] if s["name"] == sub_name_str), None)
        if sub_entry is None:
            sub_entry = {"name": sub_name_str, "efficiency": 0.0}
            entry["subs"].append(sub_entry)
        sub_entry["efficiency"] += daily_efficiency

    sorted_categories: list[tuple[str, _CategoryEfficiency]] = sorted(
        category_efficiency.items(), key=lambda item: item[1]["total"], reverse=True
    )

    main_labels = [item[0] for item in sorted_categories]
    main_data = [round(item[1]["total"], 2) for item in sorted_categories]

    sub_data = {
        cat_name: {
            "labels": [
                sub["name"]
                for sub in sorted(
                    cat_info["subs"], key=lambda x: x["efficiency"], reverse=True
                )
            ],
            "data": [
                round(sub["efficiency"], 2)
                for sub in sorted(
                    cat_info["subs"], key=lambda x: x["efficiency"], reverse=True
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

    def _iter_days(start: date, end: date):
        cur = start
        while cur <= end:
            yield cur
            cur += timedelta(days=1)

    def _week_start(d: date) -> date:
        return d - timedelta(days=d.weekday())

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
