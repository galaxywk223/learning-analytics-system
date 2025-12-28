"""
倒计时API蓝图
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import CountdownEvent
import pytz  # type: ignore[import-untyped]

bp = Blueprint("countdowns", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def get_countdowns():
    """获取所有倒计时事件 (增强: 计算剩余天数/进度百分比/状态标签)"""
    current_user_id = get_jwt_identity()
    utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)

    events = (
        CountdownEvent.query.filter_by(user_id=current_user_id)
        .order_by(CountdownEvent.target_datetime_utc.asc())
        .all()
    )

    payload = []
    for ev in events:
        # 确保时区
        target_dt = ev.target_datetime_utc
        if target_dt.tzinfo is None:
            target_dt = pytz.utc.localize(target_dt)

        # 计算剩余时间
        remaining = target_dt - utc_now
        remaining_days = remaining.days
        is_expired = remaining.total_seconds() < 0

        # 计算进度百分比 (基于 created_at 到 target 的时间区间)
        progress_percentage = None
        if ev.created_at_utc:
            start_dt = ev.created_at_utc
            if start_dt.tzinfo is None:
                start_dt = pytz.utc.localize(start_dt)
            total_span = target_dt - start_dt
            elapsed_span = utc_now - start_dt
            if total_span.total_seconds() > 0:
                progress_percentage = min(
                    (elapsed_span.total_seconds() / total_span.total_seconds()) * 100,
                    100,
                )
            else:
                progress_percentage = 100

        # 状态标签 (与旧UI保持一致: urgent <1天, warning <7天, normal 其他, expired 独立)
        if is_expired:
            card_status = "expired"
        elif remaining.days < 1:
            card_status = "urgent"
        elif remaining.days < 7:
            card_status = "warning"
        else:
            card_status = "normal"

        base = ev.to_dict()
        base.update(
            {
                "remaining_days": remaining_days if not is_expired else 0,
                "is_expired": is_expired,
                "progress_percentage": progress_percentage,
                "card_status": card_status,
            }
        )
        payload.append(base)

    return jsonify({"success": True, "countdowns": payload}), 200


@bp.route("/<int:countdown_id>", methods=["GET"])
@jwt_required()
def get_countdown(countdown_id):
    """获取单个倒计时事件"""
    current_user_id = get_jwt_identity()
    event = CountdownEvent.query.filter_by(
        id=countdown_id, user_id=current_user_id
    ).first()

    if not event:
        return jsonify({"success": False, "message": "倒计时事件不存在"}), 404

    return jsonify({"success": True, "countdown": event.to_dict()}), 200


@bp.route("", methods=["POST"])
@jwt_required()
def create_countdown():
    """创建倒计时事件"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get("title") or not data.get("target_datetime_utc"):
        return jsonify({"success": False, "message": "标题和目标时间为必填项"}), 400

    try:
        event = CountdownEvent(
            title=data["title"],
            target_datetime_utc=datetime.fromisoformat(
                data["target_datetime_utc"].replace("Z", "+00:00")
            ),
            user_id=current_user_id,
        )
        db.session.add(event)
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "倒计时事件创建成功",
                "countdown": event.to_dict(),
            }
        ), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Countdown creation error: {e}")
        return jsonify({"success": False, "message": "创建失败"}), 500


@bp.route("/<int:countdown_id>", methods=["PUT"])
@jwt_required()
def update_countdown(countdown_id):
    """更新倒计时事件"""
    current_user_id = get_jwt_identity()
    event = CountdownEvent.query.filter_by(
        id=countdown_id, user_id=current_user_id
    ).first()

    if not event:
        return jsonify({"success": False, "message": "倒计时事件不存在"}), 404

    data = request.get_json()

    try:
        if "title" in data:
            event.title = data["title"]
        if "target_datetime_utc" in data:
            event.target_datetime_utc = datetime.fromisoformat(
                data["target_datetime_utc"].replace("Z", "+00:00")
            )

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "倒计时事件更新成功",
                "countdown": event.to_dict(),
            }
        ), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Countdown update error: {e}")
        return jsonify({"success": False, "message": "更新失败"}), 500


@bp.route("/<int:countdown_id>", methods=["DELETE"])
@jwt_required()
def delete_countdown(countdown_id):
    """删除倒计时事件"""
    current_user_id = get_jwt_identity()
    event = CountdownEvent.query.filter_by(
        id=countdown_id, user_id=current_user_id
    ).first()

    if not event:
        return jsonify({"success": False, "message": "倒计时事件不存在"}), 404

    try:
        db.session.delete(event)
        db.session.commit()

        return jsonify({"success": True, "message": "倒计时事件已删除"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Countdown deletion error: {e}")
        return jsonify({"success": False, "message": "删除失败"}), 500
