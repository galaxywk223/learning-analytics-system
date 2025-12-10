"""用户API蓝图"""

import os
from datetime import datetime, date as _date
import pytz as _pytz
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from sqlalchemy import func
from app import db
from app.models import (
    User,
    Setting,
    LogEntry,
    Milestone,
    CountdownEvent,
    Stage,
    Motto,
)
import random

bp = Blueprint("users", __name__)

# ---------------- Dashboard Summary Endpoint -----------------


@bp.route("/dashboard/summary", methods=["GET"])
@jwt_required()
def dashboard_summary():
    """聚合仪表盘摘要信息，减少前端多次请求。

    返回字段：
      greeting: 基于当前小时的问候（前端也可自行计算）
      today_duration_minutes / hours
      next_countdown: {title, remaining_days} or null
      pending_todos
      milestones_count
      daily_plan: {completed, total}
      random_motto: {id, content} or null
    """
    current_user_id = get_jwt_identity()
    # 今日学习总时长
    today = _date.today()
    today_minutes = (
        LogEntry.query.join(Stage)
        .filter(Stage.user_id == current_user_id, LogEntry.log_date == today)
        .with_entities(func.sum(LogEntry.actual_duration))
        .scalar()
        or 0
    )
    hours, minutes = divmod(today_minutes, 60)

    total_records = (
        LogEntry.query.join(Stage)
        .filter(Stage.user_id == current_user_id)
        .count()
    )

    latest_entry = (
        LogEntry.query.join(Stage)
        .filter(Stage.user_id == current_user_id)
        .order_by(LogEntry.log_date.desc(), LogEntry.created_at.desc())
        .first()
    )
    latest_record_date = (
        latest_entry.log_date.isoformat() if latest_entry and latest_entry.log_date else None
    )

    # 下一个倒计时事件
    from datetime import datetime as _dt
    import pytz

    utc_now = _dt.utcnow().replace(tzinfo=pytz.utc)
    next_event_query = CountdownEvent.query.filter(
        CountdownEvent.user_id == current_user_id,
        CountdownEvent.target_datetime_utc > utc_now,
    )
    next_event = next_event_query.order_by(
        CountdownEvent.target_datetime_utc.asc()
    ).first()
    countdown_total = CountdownEvent.query.filter_by(user_id=current_user_id).count()
    next_countdown_payload = None
    if next_event:
        target_dt = next_event.target_datetime_utc
        if target_dt.tzinfo is None:
            target_dt = pytz.utc.localize(target_dt)
        remaining_days = (target_dt - utc_now).days + 1
        next_countdown_payload = {
            "title": next_event.title,
            "remaining_days": remaining_days,
        }

    # 待办数量
    pending_todos = 0

    # 里程碑数量
    milestones_count = Milestone.query.filter_by(user_id=current_user_id).count()

    # 今日计划完成统计
    # 每日计划与格言功能已屏蔽，相关统计暂不返回

    # 问候语 (可选, 简化为前端展示即可)
    tz = _pytz.timezone("Asia/Shanghai")
    current_hour = _dt.now(tz).hour
    if 5 <= current_hour < 12:
        greeting = "早上好"
    elif 12 <= current_hour < 18:
        greeting = "下午好"
    else:
        greeting = "晚上好"

    return jsonify(
        {
            "success": True,
            "data": {
                "greeting": greeting,
                "today_duration_minutes": today_minutes,
                "today_duration_formatted": f"{hours}h {minutes}m"
                if hours > 0
                else f"{minutes}m",
                "total_records": total_records,
                "latest_record_date": latest_record_date,
                "countdown_total": countdown_total,
                "next_countdown": next_countdown_payload,
                "pending_todos": pending_todos,
                "milestones_count": milestones_count,
                "daily_plan": {"completed": 0, "total": 0},
                # "daily_plan": {"completed": completed_today, "total": total_today},  # 屏蔽
                # 恢复随机格言（与旧项目结构一致，仅返回 id 与 content）
                "random_motto": (
                    lambda _all: (
                        (
                            lambda _rnd: {"id": _rnd.id, "content": _rnd.content}
                            if _rnd
                            else None
                        )(random.choice(_all) if _all else None)
                    )
                )(Motto.query.filter_by(user_id=current_user_id).all()),
            },
        }
    ), 200


# 允许的文件扩展名
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename, allowed_extensions):
    """检查文件扩展名是否允许"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


@bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """获取用户档案"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"success": False, "message": "用户不存在"}), 404

    return jsonify({"success": True, "user": user.to_dict()}), 200


@bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """更新用户档案"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"success": False, "message": "用户不存在"}), 404

    data = request.get_json()

    if "username" in data:
        # 检查用户名是否已被使用
        existing = User.query.filter(
            User.username == data["username"], User.id != user.id
        ).first()
        if existing:
            return jsonify({"success": False, "message": "用户名已被使用"}), 409
        user.username = data["username"]

    if "email" in data:
        # 检查邮箱是否已被使用
        existing = User.query.filter(
            User.email == data["email"], User.id != user.id
        ).first()
        if existing:
            return jsonify({"success": False, "message": "邮箱已被使用"}), 409
        user.email = data["email"]

    try:
        db.session.commit()
        return jsonify(
            {"success": True, "message": "档案更新成功", "user": user.to_dict()}
        ), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Profile update error: {e}")
        return jsonify({"success": False, "message": "更新失败"}), 500


@bp.route("/settings", methods=["GET"])
@jwt_required()
def get_settings():
    """获取用户设置"""
    current_user_id = get_jwt_identity()
    settings = Setting.query.filter_by(user_id=current_user_id).all()

    # Filter out background_image and theme if they exist in DB but we don't want to send them
    data = {
        s.key: s.value
        for s in settings
        if s.key not in ["background_image", "theme"]
    }

    return jsonify({"success": True, "settings": data}), 200


@bp.route("/settings", methods=["POST"])
@jwt_required()
def update_settings():
    """更新用户设置"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "请提供设置数据"}), 400

    try:
        # Ignore background_image and theme in updates
        for forbidden in ["background_image", "theme"]:
            if forbidden in data:
                del data[forbidden]

        for key, value in data.items():
            setting = Setting.query.filter_by(key=key, user_id=current_user_id).first()
            if setting:
                setting.value = str(value)
            else:
                setting = Setting(key=key, value=str(value), user_id=current_user_id)
                db.session.add(setting)

        db.session.commit()

        return jsonify({"success": True, "message": "设置已更新"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Settings update error: {e}")
        return jsonify({"success": False, "message": "更新失败"}), 500



