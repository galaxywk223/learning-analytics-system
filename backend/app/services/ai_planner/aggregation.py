from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Dict, List, Optional

from app.models import DailyData, LogEntry, Stage, SubCategory

from .countdown import _build_countdown_context
from .efficiency import _compute_efficiency_baseline


def _aggregate_learning_data(
    user_id: int,
    start_date: Optional[date],
    end_date: Optional[date],
    stage: Optional[Stage],
) -> Dict:
    """
    Aggregate learning data in the given period.
    """
    logs_query = (
        LogEntry.query.join(Stage, LogEntry.stage_id == Stage.id)
        .filter(Stage.user_id == user_id)
        .order_by(LogEntry.log_date.asc(), LogEntry.id.asc())
    )
    if stage:
        logs_query = logs_query.filter(LogEntry.stage_id == stage.id)
    if start_date:
        logs_query = logs_query.filter(LogEntry.log_date >= start_date)
    if end_date:
        logs_query = logs_query.filter(LogEntry.log_date <= end_date)

    logs = logs_query.all()
    countdown_context = _build_countdown_context(user_id, start_date, end_date)
    efficiency_baseline = _compute_efficiency_baseline(user_id, end_date or date.today())

    total_minutes = sum(int(log.actual_duration or 0) for log in logs)
    total_sessions = len(logs)

    daily_minutes: Dict[date, int] = defaultdict(int)
    weekday_minutes: Dict[int, int] = defaultdict(int)  # 0=Mon ... 6=Sun
    hour_minutes: Dict[int, int] = defaultdict(int)  # 0-23
    mood_sum = 0
    mood_count = 0
    task_counter: Counter[str] = Counter()
    category_minutes: Dict[str, int] = defaultdict(int)

    subcategory_ids = {
        log.subcategory_id for log in logs if log.subcategory_id is not None
    }
    subcategory_map: Dict[int, SubCategory] = {}
    if subcategory_ids:
        subcategory_map = {
            sub.id: sub
            for sub in SubCategory.query.filter(SubCategory.id.in_(subcategory_ids)).all()
        }

    for log in logs:
        minutes = int(log.actual_duration or 0)
        log_day = log.log_date
        daily_minutes[log_day] += minutes
        try:
            # 「活跃时段」统计：使用开始时间 hour，如果缺失则跳过
            if getattr(log, "start_time", None):
                hour = int(str(log.start_time)[0:2])  # 支持 "HH:MM:SS" 或 datetime
                if 0 <= hour <= 23:
                    hour_minutes[hour] += minutes
        except Exception:
            pass
        try:
            weekday = log_day.weekday()
            weekday_minutes[weekday] += minutes
        except Exception:
            pass

        task_name = (log.task or '').strip() or '未命名任务'

        category_name = '未分类'
        subcategory_name = None
        if log.subcategory_id and log.subcategory_id in subcategory_map:
            subcategory = subcategory_map[log.subcategory_id]
            if getattr(subcategory, 'category', None) and subcategory.category.name:
                category_name = subcategory.category.name
            elif subcategory.name:
                category_name = subcategory.name
            if subcategory.name:
                subcategory_name = subcategory.name
        elif log.legacy_category:
            category_name = log.legacy_category

        path_parts = [part for part in [category_name, subcategory_name] if part]
        path_label = "-".join(path_parts) if path_parts else "未分类"
        full_task_label = f"[{path_label}] {task_name}"
        task_counter[full_task_label] += minutes

        if log.mood is not None:
            mood_sum += log.mood
            mood_count += 1

        category_minutes[category_name] += minutes

    average_mood = round(mood_sum / mood_count, 2) if mood_count else None

    efficiency_query = (
        DailyData.query.join(Stage, DailyData.stage_id == Stage.id)
        .filter(Stage.user_id == user_id)
        .order_by(DailyData.log_date.asc(), DailyData.id.asc())
    )
    if stage:
        efficiency_query = efficiency_query.filter(DailyData.stage_id == stage.id)
    if start_date:
        efficiency_query = efficiency_query.filter(DailyData.log_date >= start_date)
    if end_date:
        efficiency_query = efficiency_query.filter(DailyData.log_date <= end_date)

    efficiency_rows = efficiency_query.all()
    efficiency_values = [
        row.efficiency for row in efficiency_rows if row.efficiency is not None
    ]
    average_efficiency = (
        round(sum(efficiency_values) / len(efficiency_values), 2)
        if efficiency_values
        else None
    )

    daily_efficiency = {
        row.log_date: row.efficiency
        for row in efficiency_rows
        if row.efficiency is not None
    }

    all_days = sorted(set(daily_minutes.keys()) | set(daily_efficiency.keys()))
    daily_stats = [
        {
            'date': day.isoformat(),
            'duration_minutes': daily_minutes.get(day, 0),
            'efficiency': daily_efficiency.get(day),
        }
        for day in all_days
    ]

    category_stats = [
        {
            'name': name,
            'minutes': minutes,
            'hours': round(minutes / 60, 2),
            'percentage': round(minutes / max(total_minutes, 1) * 100, 1),
        }
        for name, minutes in sorted(
            category_minutes.items(), key=lambda item: item[1], reverse=True
        )
    ]

    top_tasks = [
        {
            'task': task,
            'minutes': minutes,
            'hours': round(minutes / 60, 2),
            'percentage': round(minutes / max(total_minutes, 1) * 100, 1),
        }
        for task, minutes in task_counter.most_common(5)
    ]

    active_days = len(daily_minutes)
    idle_days: List[str] = []
    if start_date and end_date:
        current = start_date
        while current <= end_date:
            if current not in daily_minutes:
                idle_days.append(current.isoformat())
            current += timedelta(days=1)

    # 活跃占比与学习打卡连击（当前/最长连续）
    total_days = None
    active_ratio = None
    current_streak = 0
    longest_streak = 0
    if start_date and end_date:
        total_days = (end_date - start_date).days + 1
        if total_days > 0:
            active_ratio = round(active_days / total_days, 3)
        # 计算 streak
        run = 0
        current = start_date
        while current <= end_date:
            if current in daily_minutes and daily_minutes[current] > 0:
                run += 1
                longest_streak = max(longest_streak, run)
            else:
                run = 0
            current += timedelta(days=1)
        # 计算当前连击：从区间末尾往前
        run = 0
        current = end_date
        while current >= start_date:
            if current in daily_minutes and daily_minutes[current] > 0:
                run += 1
                current -= timedelta(days=1)
            else:
                break
        current_streak = run

    # 将 weekday/hour 统计转为列表并补齐缺失键
    weekday_stats = [
        {
            "weekday": i,  # 0=Mon
            "minutes": int(weekday_minutes.get(i, 0)),
            "hours": round(weekday_minutes.get(i, 0) / 60, 2),
        }
        for i in range(7)
    ]
    hour_stats = [
        {
            "hour": h,
            "minutes": int(hour_minutes.get(h, 0)),
            "hours": round(hour_minutes.get(h, 0) / 60, 2),
        }
        for h in range(24)
    ]

    return {
        'total_minutes': total_minutes,
        'total_hours': round(total_minutes / 60, 2) if total_minutes else 0,
        'total_sessions': total_sessions,
        'average_daily_minutes': (
            round(total_minutes / active_days, 2) if active_days else 0
        ),
        'average_efficiency': average_efficiency,
        'average_mood': average_mood,
        'daily_stats': daily_stats,
        'category_stats': category_stats,
        'top_tasks': top_tasks,
        'idle_days': idle_days,
        'total_days': total_days,
        'active_days': active_days,
        'active_ratio': active_ratio,
        'streak_current': current_streak,
        'streak_longest': longest_streak,
        'weekday_stats': weekday_stats,
        'hour_stats': hour_stats,
        'countdown_context': countdown_context,
        'efficiency_baseline': efficiency_baseline,
    }


__all__ = ["_aggregate_learning_data"]
