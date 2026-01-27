# 文件路径: backend/app/services/record_service.py
import math
from datetime import date, timedelta
from itertools import groupby
from numbers import Number
from typing import Any

from flask import current_app
from sqlalchemy import tuple_
from sqlalchemy.orm import joinedload

from app import db
from app.models import Stage, LogEntry, WeeklyData, DailyData, Category, SubCategory
from .helpers import get_custom_week_info


def get_stage_for_date(user_id, log_date):
    """根据日期选择所属阶段：start_date <= log_date 的最新阶段。"""
    return (
        Stage.query.filter(
            Stage.user_id == user_id,
            Stage.start_date <= log_date,
        )
        .order_by(Stage.start_date.desc())
        .first()
    )


def ensure_log_stage_consistency(user_id):
    """
    Ensure all logs for a user are assigned to the correct stage based on their date.
    This should be called when stages are modified (created, updated dates, deleted).
    """
    try:
        current_app.logger.info(f"Starting stage consistency check for user {user_id}")
        
        # Performance optimization: Fetch all stages and sort them once
        stages = Stage.query.filter_by(user_id=user_id).order_by(Stage.start_date.desc()).all()
        
        if not stages:
            current_app.logger.warning(f"No stages found for user {user_id}, skipping consistency check")
            return

        # Fetch all logs
        logs = LogEntry.query.join(Stage).filter(Stage.user_id == user_id).all()
        
        updates_count = 0
        
        for log in logs:
            # Find correct stage in memory
            correct_stage = None
            for stage in stages:
                if stage.start_date <= log.log_date:
                    correct_stage = stage
                    break
            
            if correct_stage and log.stage_id != correct_stage.id:
                old_stage_id = log.stage_id
                log.stage_id = correct_stage.id
                updates_count += 1
                # Note: We might want to update efficiency stats here too if we want to be 100% correct,
                # but recalculating everything might be heavy. 
                # Ideally, we should mark involved stages for recalculation.
                
        if updates_count > 0:
            db.session.commit()
            
            # Recalculate efficiency for ALL stages to be safe and consistent
            # This is heavy but ensures data integrity after a structural change
            for stage in stages:
                recalculate_efficiency_for_stage(stage)
                
            current_app.logger.info(f"Updated {updates_count} logs to correct stages for user {user_id}")
        else:
            current_app.logger.info(f"No inconsistencies found for user {user_id}")
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error ensuring log stage consistency: {e}", exc_info=True)



def _normalize_duration_minutes(value):
    """将存储的时长统一转换为分钟，兼容历史小时制浮点数。"""
    if value is None:
        return 0

    if isinstance(value, Number):
        numeric_value = float(value)  # type: ignore[arg-type]
        if not math.isfinite(numeric_value):
            return 0

        if not math.isclose(numeric_value, round(numeric_value), rel_tol=1e-9):
            minutes = int(round(numeric_value * 60))
        else:
            minutes = int(round(numeric_value))

        return max(minutes, 0)

    try:
        numeric_value = float(value)
        return max(int(round(numeric_value)), 0)
    except (TypeError, ValueError):
        return 0


def format_record_for_response(record, stage=None):
    """序列化单条 LogEntry 记录，供 API / 表单使用。"""
    total_minutes = _normalize_duration_minutes(record.actual_duration)
    stage_obj = stage or getattr(record, "stage", None)

    data = {
        "id": record.id,
        "task": record.task,
        "log_date": record.log_date.isoformat() if record.log_date else None,
        "time_slot": record.time_slot,
        "actual_duration": total_minutes,
        "duration_hours": total_minutes // 60,
        "duration_minutes": total_minutes % 60,
        "mood": record.mood,
        "notes": record.notes,
        "legacy_category": record.legacy_category,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "stage_id": stage_obj.id if stage_obj else record.stage_id,
        "subcategory_id": record.subcategory_id,
    }

    if stage_obj:
        data["stage"] = {
            "id": stage_obj.id,
            "name": stage_obj.name,
            "start_date": stage_obj.start_date.isoformat()
            if stage_obj.start_date
            else None,
        }
    else:
        data["stage"] = None

    subcategory = getattr(record, "subcategory", None)
    if subcategory:
        category = subcategory.category
        data["subcategory"] = {
            "id": subcategory.id,
            "name": subcategory.name,
            "category_id": subcategory.category_id,
            "category": {"id": category.id, "name": category.name} if category else None,
        }
        data["category_id"] = subcategory.category_id
    else:
        data["subcategory"] = None
        data["category_id"] = None

    return data


def _calculate_daily_efficiency_score(log_date, stage_id):
    """
    按"方案C:对数加权模型"计算每日效率分。
    公式: 每日效率 = (加权平均心情) × log(1 + 总学习小时数)
    """
    logs_for_day = LogEntry.query.filter_by(log_date=log_date, stage_id=stage_id).all()

    if not logs_for_day:
        return 0.0

    durations = [_normalize_duration_minutes(log.actual_duration) for log in logs_for_day]
    total_duration_minutes = sum(durations)

    if total_duration_minutes == 0:
        return 0.0

    weighted_mood_duration_sum = sum(
        duration * (log.mood or 3) for duration, log in zip(durations, logs_for_day)
    )
    average_mood = weighted_mood_duration_sum / total_duration_minutes
    total_hours = total_duration_minutes / 60.0
    final_score = average_mood * math.log1p(total_hours)

    return final_score


def _get_or_create_daily_data(log_date, stage_id, score):
    daily_data = DailyData.query.filter_by(log_date=log_date, stage_id=stage_id).first()
    if not daily_data:
        daily_data = DailyData(log_date=log_date, stage_id=stage_id)
        db.session.add(daily_data)
    daily_data.efficiency = score


def _get_or_create_weekly_data(year, week_num, stage_id, score):
    weekly_data = WeeklyData.query.filter_by(
        year=year, week_num=week_num, stage_id=stage_id
    ).first()
    if not weekly_data:
        weekly_data = WeeklyData(year=year, week_num=week_num, stage_id=stage_id)
        db.session.add(weekly_data)
    weekly_data.efficiency = score


def update_efficiency_for_date(log_date, stage):
    """
    Incrementally updates the efficiency score for a specific date and its corresponding week.
    This is much faster than recalculating the entire stage.
    """
    try:
        daily_score = _calculate_daily_efficiency_score(log_date, stage.id)
        _get_or_create_daily_data(log_date, stage.id, daily_score)

        year, week_num = get_custom_week_info(log_date, stage.start_date)

        week_start_date = stage.start_date + timedelta(weeks=week_num - 1)
        week_end_date = week_start_date + timedelta(days=6)

        daily_scores_for_week = (
            db.session.query(DailyData.efficiency)
            .filter(
                DailyData.stage_id == stage.id,
                DailyData.log_date.between(week_start_date, week_end_date),
            )
            .all()
        )

        total_score = sum(
            item[0] for item in daily_scores_for_week if item[0] is not None
        )
        count = len(daily_scores_for_week)
        average_score = total_score / count if count > 0 else 0.0

        _get_or_create_weekly_data(year, week_num, stage.id, average_score)

        db.session.commit()
        current_app.logger.info(
            f"Incrementally updated efficiency for date: {log_date} in stage '{stage.name}'."
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error in update_efficiency_for_date for date '{log_date}': {e}",
            exc_info=True,
        )


def recalculate_efficiency_for_stage(stage):
    try:
        all_logs = stage.log_entries.all()
        DailyData.query.filter_by(stage_id=stage.id).delete()
        WeeklyData.query.filter_by(stage_id=stage.id).delete()
        db.session.commit()

        if not all_logs:
            return

        unique_log_dates = sorted(list(set(log.log_date for log in all_logs)))
        daily_efficiencies_map = {}
        for log_date in unique_log_dates:
            score = _calculate_daily_efficiency_score(log_date, stage.id)
            _get_or_create_daily_data(log_date, stage.id, score)
            daily_efficiencies_map[log_date] = score

        db.session.commit()

        next_stage = (
            Stage.query.filter(
                Stage.user_id == stage.user_id, Stage.start_date > stage.start_date
            )
            .order_by(Stage.start_date.asc())
            .first()
        )
        stage_end_date = (
            (next_stage.start_date - timedelta(days=1)) if next_stage else date.today()
        )

        unique_weeks = sorted(
            list(
                set(get_custom_week_info(d, stage.start_date) for d in unique_log_dates)
            )
        )
        for year, week_num in unique_weeks:
            theoretical_week_start = stage.start_date + timedelta(weeks=week_num - 1)
            theoretical_week_end = theoretical_week_start + timedelta(days=6)
            effective_start = max(theoretical_week_start, stage.start_date)
            effective_end = min(theoretical_week_end, stage_end_date, date.today())
            days_in_week = (
                (effective_end - effective_start).days + 1
                if effective_end >= effective_start
                else 0
            )

            total_score = sum(
                daily_efficiencies_map.get(effective_start + timedelta(days=i), 0)
                for i in range(days_in_week)
            )
            average_score = total_score / days_in_week if days_in_week > 0 else 0
            _get_or_create_weekly_data(year, week_num, stage.id, average_score)

        db.session.commit()
        current_app.logger.info(
            f"Successfully recalculated efficiency for stage '{stage.name}'."
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error in recalculate_efficiency_for_stage for stage '{stage.name}': {e}",
            exc_info=True,
        )


def get_structured_logs_for_stage(stage, sort_order="desc"):
    is_reverse = sort_order == "desc"

    next_stage = (
        Stage.query.filter(
            Stage.user_id == stage.user_id, Stage.start_date > stage.start_date
        )
        .order_by(Stage.start_date.asc())
        .first()
    )
    stage_end_date = (
        (next_stage.start_date - timedelta(days=1)) if next_stage else None
    )

    log_query = (
        LogEntry.query.join(Stage)
        .filter(
            Stage.user_id == stage.user_id,
            LogEntry.log_date >= stage.start_date,
            LogEntry.log_date <= stage_end_date,
        )
        if stage_end_date
        else LogEntry.query.join(Stage).filter(
            Stage.user_id == stage.user_id,
            LogEntry.log_date >= stage.start_date,
        )
    )

    log_query = log_query.options(
        joinedload(LogEntry.subcategory).joinedload(SubCategory.category)
    ).order_by(LogEntry.log_date.asc(), LogEntry.id.asc())

    all_logs = log_query.all()

    touched_stage_ids = set()
    for log in all_logs:
        if log.stage_id != stage.id:
            touched_stage_ids.add(log.stage_id)
            log.stage_id = stage.id

    if touched_stage_ids:
        touched_stage_ids.add(stage.id)
        db.session.commit()
        for stage_id in sorted(touched_stage_ids):
            touched_stage = Stage.query.filter_by(id=stage_id, user_id=stage.user_id).first()
            if touched_stage:
                recalculate_efficiency_for_stage(touched_stage)

    structured_logs: list[dict[str, Any]] = []
    if not all_logs:
        return structured_logs

    log_dates = {log.log_date for log in all_logs}
    week_keys = {
        get_custom_week_info(log.log_date, stage.start_date) for log in all_logs
    }

    day_data_map = {}
    if log_dates:
        daily_rows = (
            DailyData.query.filter(
                DailyData.stage_id == stage.id, DailyData.log_date.in_(log_dates)
            ).all()
        )
        day_data_map = {row.log_date: row for row in daily_rows}

    week_data_map = {}
    if week_keys:
        weekly_rows = (
            WeeklyData.query.filter(
                WeeklyData.stage_id == stage.id,
                tuple_(WeeklyData.year, WeeklyData.week_num).in_(list(week_keys)),
            ).all()
        )
        week_data_map = {(row.year, row.week_num): row for row in weekly_rows}

    logs_by_week_iter = groupby(
        all_logs, key=lambda log: get_custom_week_info(log.log_date, stage.start_date)
    )
    for (year, week_num), week_logs in logs_by_week_iter:
        week_logs_list = list(week_logs)
        days_in_week = []
        logs_by_day_iter = groupby(week_logs_list, key=lambda log: log.log_date)
        for day_date, day_logs in logs_by_day_iter:
            day_logs_list = list(day_logs)
            day_data = day_data_map.get(day_date)
            days_in_week.append(
                {
                    "date": day_date,
                    "efficiency": day_data.efficiency if day_data else 0,
                    "logs": [
                        format_record_for_response(log, stage=stage)
                        for log in day_logs_list
                    ],
                }
            )
        week_data = week_data_map.get((year, week_num))
        structured_logs.append(
            {
                "year": year,
                "week_num": week_num,
                "efficiency": week_data.efficiency if week_data else 0,
                "days": sorted(
                    days_in_week, key=lambda d: d["date"], reverse=is_reverse
                ),
            }
        )
    return sorted(
        structured_logs, key=lambda w: (w["year"], w["week_num"]), reverse=is_reverse
    )


def calculate_record_statistics(records):
    """计算记录统计信息（用于 /records/stats）。"""
    total_records = len(records)
    total_minutes = sum(
        _normalize_duration_minutes(record.actual_duration) for record in records
    )
    avg_minutes = round(total_minutes / total_records, 2) if total_records else 0
    mood_values = [record.mood for record in records if record.mood is not None]
    avg_mood = (
        round(sum(mood_values) / len(mood_values), 2) if mood_values else None
    )

    return {
        "total_records": total_records,
        "total_minutes": total_minutes,
        "total_hours": round(total_minutes / 60, 2),
        "avg_minutes": avg_minutes,
        "avg_mood": avg_mood,
    }

def add_log_for_stage(stage_id, user, form_data):
    # Auto-assign stage based on date
    log_date_obj = date.fromisoformat(form_data["log_date"])
    stage = get_stage_for_date(user.id, log_date_obj)

    if not stage:
        return False, "无法找到匹配日期的学习阶段，请检查日期或先创建对应阶段。", None

    try:
        subcategory_id = form_data.get("subcategory_id", type=int)
        if subcategory_id:
            subcategory = (
                SubCategory.query.join(Category)
                .filter(SubCategory.id == subcategory_id, Category.user_id == user.id)
                .first()
            )
            if not subcategory:
                return False, "选择了无效的分类。", None

        hours_str = form_data.get("duration_hours", "0")
        minutes_str = form_data.get("duration_minutes", "0")
        hours = int(hours_str) if hours_str and hours_str.strip() else 0
        minutes = int(minutes_str) if minutes_str and minutes_str.strip() else 0
        total_duration = (hours * 60) + minutes

        new_log = LogEntry(
            stage_id=stage.id,
            log_date=log_date_obj,
            task=form_data.get("task"),
            time_slot=form_data.get("time_slot"),
            notes=form_data.get("notes"),
            actual_duration=total_duration,
            mood=form_data.get("mood", type=int),
            subcategory_id=subcategory_id,
        )
        db.session.add(new_log)

        db.session.flush()
        new_log_id = new_log.id
        db.session.commit()

        update_efficiency_for_date(new_log.log_date, stage)

        return True, "新纪录添加成功!", new_log_id

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Add log error: {e}", exc_info=True)

        return False, f"发生错误: {e}", None


def update_log_for_user(log_id, user, form_data):
    log = get_log_entry_for_user(log_id, user)
    if not log:
        return False, "未找到要编辑的记录或无权访问。"
    try:
        old_date = log.log_date
        new_date = date.fromisoformat(form_data.get("log_date"))
        
        # Recalculate stage if date changed or just to be safe
        new_stage = get_stage_for_date(user.id, new_date)
        if not new_stage:
             return False, "无法找到匹配新日期的学习阶段。"
             
        log.stage_id = new_stage.id
        stage = new_stage # Update local ref for efficiency update

        subcategory_id = form_data.get("subcategory_id", type=int)
        if subcategory_id:
            subcategory = (
                SubCategory.query.join(Category)
                .filter(SubCategory.id == subcategory_id, Category.user_id == user.id)
                .first()
            )
            if not subcategory:
                return False, "选择了无效的分类。"

        hours_str = form_data.get("duration_hours", "0")
        minutes_str = form_data.get("duration_minutes", "0")
        hours = int(hours_str) if hours_str and hours_str.strip() else 0
        minutes = int(minutes_str) if minutes_str and minutes_str.strip() else 0
        total_duration = (hours * 60) + minutes

        log.log_date = new_date
        log.task = form_data.get("task")
        log.time_slot = form_data.get("time_slot")
        log.notes = form_data.get("notes")
        log.actual_duration = total_duration
        log.mood = form_data.get("mood", type=int)
        log.subcategory_id = subcategory_id

        db.session.commit()

        update_efficiency_for_date(new_date, stage)

        if old_date != new_date:
            old_stage = get_stage_for_date(user.id, old_date)
            if old_stage:
                update_efficiency_for_date(old_date, old_stage)

        return True, "记录更新成功!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update log error: {e}", exc_info=True)
        return False, f"更新时发生错误: {e}"


def delete_log_for_user(log_id, user):
    log = get_log_entry_for_user(log_id, user)
    if not log:
        return False, "未找到要删除的记录或无权访问。"
    try:
        stage = log.stage

        date_to_update = log.log_date

        db.session.delete(log)
        db.session.commit()

        update_efficiency_for_date(date_to_update, stage)
        return True, "记录已删除。"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete log error: {e}", exc_info=True)
        return False, f"删除时发生错误: {e}"


def get_log_entry_for_user(log_id, user):
    return (
        LogEntry.query.join(Stage)
        .filter(Stage.user_id == user.id, LogEntry.id == log_id)
        .first()
    )
