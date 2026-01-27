"""
阶段API蓝图
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import Stage
from app.services import record_service

bp = Blueprint("stages", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def get_stages():
    """获取所有阶段"""
    current_user_id = get_jwt_identity()
    stages = (
        Stage.query.filter_by(user_id=current_user_id)
        .order_by(Stage.start_date.desc())
        .all()
    )

    return jsonify(
        {"success": True, "stages": [stage.to_dict() for stage in stages]}
    ), 200


@bp.route("/<int:stage_id>", methods=["GET"])
@jwt_required()
def get_stage(stage_id):
    """获取单个阶段"""
    current_user_id = get_jwt_identity()
    stage = Stage.query.filter_by(id=stage_id, user_id=current_user_id).first()

    if not stage:
        return jsonify({"success": False, "message": "阶段不存在"}), 404

    return jsonify({"success": True, "stage": stage.to_dict()}), 200


@bp.route("", methods=["POST"])
@jwt_required()
def create_stage():
    """创建新阶段"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get("name"):
        return jsonify({"success": False, "message": "阶段名称为必填项"}), 400

    try:
        stage = Stage(
            name=data["name"],
            start_date=datetime.fromisoformat(data["start_date"]).date()
            if data.get("start_date")
            else datetime.now().date(),
            user_id=current_user_id,
        )
        db.session.add(stage)
        db.session.commit()

        # Update log consistency
        record_service.ensure_log_stage_consistency(current_user_id)

        return jsonify(
            {"success": True, "message": "阶段创建成功", "stage": stage.to_dict()}
        ), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Stage creation error: {e}")
        return jsonify({"success": False, "message": "创建失败"}), 500


@bp.route("/<int:stage_id>", methods=["PUT"])
@jwt_required()
def update_stage(stage_id):
    """更新阶段"""
    current_user_id = get_jwt_identity()
    stage = Stage.query.filter_by(id=stage_id, user_id=current_user_id).first()

    if not stage:
        return jsonify({"success": False, "message": "阶段不存在"}), 404

    data = request.get_json()

    try:
        if "name" in data:
            stage.name = data["name"]
        if "start_date" in data:
            stage.start_date = datetime.fromisoformat(data["start_date"]).date()

        db.session.commit()

        # Update log consistency
        record_service.ensure_log_stage_consistency(current_user_id)

        return jsonify(
            {"success": True, "message": "阶段更新成功", "stage": stage.to_dict()}
        ), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Stage update error: {e}")
        return jsonify({"success": False, "message": "更新失败"}), 500


@bp.route("/<int:stage_id>", methods=["DELETE"])
@jwt_required()
def delete_stage(stage_id):
    """删除阶段"""
    current_user_id = get_jwt_identity()
    stage = Stage.query.filter_by(id=stage_id, user_id=current_user_id).first()

    if not stage:
        return jsonify({"success": False, "message": "阶段不存在"}), 404

    try:
        db.session.delete(stage)
        db.session.commit()

        # Update log consistency
        record_service.ensure_log_stage_consistency(current_user_id)

        return jsonify({"success": True, "message": "阶段已删除"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Stage deletion error: {e}")
        return jsonify({"success": False, "message": "删除失败"}), 500
