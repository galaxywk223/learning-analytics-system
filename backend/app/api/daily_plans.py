"""
每日计划API蓝图
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date
from app import db
from app.models import DailyPlanItem

bp = Blueprint("daily_plans", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def get_daily_plans():
    """获取每日计划"""
    current_user_id = get_jwt_identity()

    plan_date = request.args.get("date")
    if plan_date:
        target_date = datetime.fromisoformat(plan_date).date()
    else:
        target_date = date.today()

    plans = (
        DailyPlanItem.query.filter_by(user_id=current_user_id, plan_date=target_date)
        .order_by(DailyPlanItem.time_slot, DailyPlanItem.created_at)
        .all()
    )

    return jsonify(
        {
            "success": True,
            "date": target_date.isoformat(),
            "plans": [plan.to_dict() for plan in plans],
        }
    ), 200


@bp.route("", methods=["POST"])
@jwt_required()
def create_daily_plan():
    """创建每日计划项"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get("content"):
        return jsonify({"success": False, "message": "内容为必填项"}), 400

    try:
        plan = DailyPlanItem(
            plan_date=datetime.fromisoformat(data["plan_date"]).date()
            if data.get("plan_date")
            else date.today(),
            content=data["content"],
            time_slot=data.get("time_slot"),
            user_id=current_user_id,
        )
        db.session.add(plan)
        db.session.commit()

        return jsonify(
            {"success": True, "message": "计划创建成功", "plan": plan.to_dict()}
        ), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Plan creation error: {e}")
        return jsonify({"success": False, "message": "创建失败"}), 500


@bp.route("/<int:plan_id>", methods=["PUT"])
@jwt_required()
def update_daily_plan(plan_id):
    """更新每日计划项"""
    current_user_id = get_jwt_identity()
    plan = DailyPlanItem.query.filter_by(id=plan_id, user_id=current_user_id).first()

    if not plan:
        return jsonify({"success": False, "message": "计划项不存在"}), 404

    data = request.get_json()

    try:
        if "content" in data:
            plan.content = data["content"]
        if "time_slot" in data:
            plan.time_slot = data["time_slot"]
        if "is_completed" in data:
            plan.is_completed = data["is_completed"]

        db.session.commit()

        return jsonify(
            {"success": True, "message": "计划更新成功", "plan": plan.to_dict()}
        ), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Plan update error: {e}")
        return jsonify({"success": False, "message": "更新失败"}), 500


@bp.route("/<int:plan_id>/toggle", methods=["POST"])
@jwt_required()
def toggle_daily_plan(plan_id):
    """切换计划项完成状态"""
    current_user_id = get_jwt_identity()
    plan = DailyPlanItem.query.filter_by(id=plan_id, user_id=current_user_id).first()

    if not plan:
        return jsonify({"success": False, "message": "计划项不存在"}), 404

    try:
        plan.is_completed = not plan.is_completed
        db.session.commit()

        return jsonify(
            {"success": True, "message": "状态更新成功", "plan": plan.to_dict()}
        ), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Plan toggle error: {e}")
        return jsonify({"success": False, "message": "更新失败"}), 500


@bp.route("/<int:plan_id>", methods=["DELETE"])
@jwt_required()
def delete_daily_plan(plan_id):
    """删除每日计划项"""
    current_user_id = get_jwt_identity()
    plan = DailyPlanItem.query.filter_by(id=plan_id, user_id=current_user_id).first()

    if not plan:
        return jsonify({"success": False, "message": "计划项不存在"}), 404

    try:
        db.session.delete(plan)
        db.session.commit()

        return jsonify({"success": True, "message": "计划项已删除"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Plan deletion error: {e}")
        return jsonify({"success": False, "message": "删除失败"}), 500
