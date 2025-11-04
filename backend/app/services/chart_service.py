"""
图表统计服务
"""

import collections
from datetime import date, timedelta
from sqlalchemy import func, desc
import numpy as np

from app import db
from app.models import Stage, LogEntry, WeeklyData, DailyData, Category, SubCategory
from .helpers import get_custom_week_info


def _calculate_sma(data, window_size=7):
    """计算简单移动平均线，能正确处理None/NaN值"""
    if not data or window_size <= 1:
        return [None] * len(data)

    numeric_data = [float(v) if v is not None else np.nan for v in data]

    if len(numeric_data) < window_size:
        return [None] * len(numeric_data)

    sma_values = []
    window = collections.deque(maxlen=window_size)
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

    weekly_data = collections.defaultdict(
        lambda: {"duration": 0, "efficiency": None, "days": 0}
    )
    for d in date_range:
        year, week_num = get_custom_week_info(d, global_start_date)
        weekly_data[(year, week_num)]["duration"] += daily_duration_map.get(d, 0)
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
    weekly_durations = [
        round(weekly_data[k]["duration"] / 60 / max(weekly_data[k]["days"], 1), 2)
        for k in sorted_week_keys
    ]
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
        category_data = {}
        for legacy_cat, duration in legacy_results:
            duration_hours = (duration or 0) / 60.0
            category_data[legacy_cat] = duration_hours

        sorted_categories = sorted(
            category_data.items(), key=lambda item: item[1], reverse=True
        )

        main_labels = [item[0] for item in sorted_categories]
        main_data = [round(item[1], 2) for item in sorted_categories]

        # legacy_category 没有子分类，drilldown 为空字典
        return {"main": {"labels": main_labels, "data": main_data}, "drilldown": {}}

    category_data = collections.defaultdict(lambda: {"total": 0, "subs": []})
    for cat_name, sub_name, duration in results:
        duration_hours = (duration or 0) / 60.0
        category_data[cat_name]["total"] += duration_hours
        category_data[cat_name]["subs"].append(
            {"name": sub_name, "duration": round(duration_hours, 2)}
        )

    sorted_categories = sorted(
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
