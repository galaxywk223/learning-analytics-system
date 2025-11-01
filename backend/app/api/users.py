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
    Todo,
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

    # 下一个倒计时事件
    from datetime import datetime as _dt
    import pytz

    utc_now = _dt.utcnow().replace(tzinfo=pytz.utc)
    next_event = (
        CountdownEvent.query.filter(
            CountdownEvent.user_id == current_user_id,
            CountdownEvent.target_datetime_utc > utc_now,
        )
        .order_by(CountdownEvent.target_datetime_utc.asc())
        .first()
    )
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
    pending_todos = Todo.query.filter_by(
        user_id=current_user_id, is_completed=False
    ).count()

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
                "next_countdown": next_countdown_payload,
                "pending_todos": pending_todos,
                "milestones_count": milestones_count,
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

    return jsonify(
        {"success": True, "settings": {s.key: s.value for s in settings}}
    ), 200


@bp.route("/settings", methods=["POST"])
@jwt_required()
def update_settings():
    """更新用户设置"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "请提供设置数据"}), 400

    try:
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


@bp.route("/upload/background", methods=["POST"])
@jwt_required()
def upload_background():
    """上传背景图片"""
    current_user_id = get_jwt_identity()

    if "file" not in request.files:
        return jsonify({"success": False, "message": "没有文件被上传"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"success": False, "message": "文件名为空"}), 400

    if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
        return jsonify(
            {"success": False, "message": "不支持的文件格式,仅支持png、jpg、jpeg、gif"}
        ), 400

    try:
        # 生成安全的文件名
        timestamp = int(datetime.now().timestamp())
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"bg_{current_user_id}_{timestamp}.{ext}"
        filename = secure_filename(filename)

        # 确保上传目录存在
        upload_folder = current_app.config.get("BACKGROUND_UPLOADS")
        if not upload_folder:
            return jsonify({"success": False, "message": "上传功能未配置"}), 500

        user_upload_dir = os.path.join(upload_folder, str(current_user_id))
        os.makedirs(user_upload_dir, exist_ok=True)

        # 保存文件
        file_path = os.path.join(user_upload_dir, filename)
        file.save(file_path)

        # 更新用户设置
        relative_path = f"{current_user_id}/{filename}"
        setting = Setting.query.filter_by(
            key="background_image", user_id=current_user_id
        ).first()
        if setting:
            setting.value = relative_path
        else:
            setting = Setting(
                key="background_image", value=relative_path, user_id=current_user_id
            )
            db.session.add(setting)

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "背景图片上传成功",
                "background_image": relative_path,
            }
        ), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Background upload error: {e}")
        return jsonify({"success": False, "message": "上传失败"}), 500


@bp.route("/upload/background", methods=["DELETE"])
@jwt_required()
def delete_background():
    """删除背景图片"""
    current_user_id = get_jwt_identity()

    try:
        setting = Setting.query.filter_by(
            key="background_image", user_id=current_user_id
        ).first()
        if setting:
            # 删除文件
            if setting.value:
                upload_folder = current_app.config.get("BACKGROUND_UPLOADS")
                file_path = os.path.join(upload_folder, setting.value)
                if os.path.exists(file_path):
                    os.remove(file_path)

            # 删除设置记录
            db.session.delete(setting)
            db.session.commit()

        return jsonify({"success": True, "message": "背景图片已删除"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Background delete error: {e}")
        return jsonify({"success": False, "message": "删除失败"}), 500
