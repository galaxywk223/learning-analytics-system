"""
座右铭API蓝图
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Motto
import random

bp = Blueprint("mottos", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def get_mottos():
    """获取所有座右铭"""
    current_user_id = get_jwt_identity()
    mottos = Motto.query.filter_by(user_id=current_user_id).all()

    return jsonify(
        {"success": True, "mottos": [motto.to_dict() for motto in mottos]}
    ), 200


@bp.route("/random", methods=["GET"])
@jwt_required()
def get_random_motto():
    """获取随机座右铭"""
    current_user_id = get_jwt_identity()
    mottos = Motto.query.filter_by(user_id=current_user_id).all()

    if not mottos:
        # 与旧项目保持默认返回文案，同时 success True，方便前端直接展示
        fallback_content = "书山有路勤为径，学海无涯苦作舟。"
        return jsonify(
            {"success": True, "content": fallback_content, "motto": None}
        ), 200

    random_motto = random.choice(mottos)
    # 兼容旧结构增加 content 字段
    return jsonify(
        {
            "success": True,
            "content": random_motto.content,
            "motto": random_motto.to_dict(),
        }
    ), 200


@bp.route("/<int:motto_id>", methods=["GET"])
@jwt_required()
def get_motto(motto_id):
    """获取单个座右铭"""
    current_user_id = get_jwt_identity()
    motto = Motto.query.filter_by(id=motto_id, user_id=current_user_id).first()

    if not motto:
        return jsonify({"success": False, "message": "座右铭不存在"}), 404

    return jsonify({"success": True, "motto": motto.to_dict()}), 200


@bp.route("", methods=["POST"])
@jwt_required()
def create_motto():
    """创建座右铭"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get("content"):
        return jsonify({"success": False, "message": "内容为必填项"}), 400

    try:
        motto = Motto(content=data["content"], user_id=current_user_id)
        db.session.add(motto)
        db.session.commit()

        return jsonify(
            {"success": True, "message": "座右铭创建成功", "motto": motto.to_dict()}
        ), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Motto creation error: {e}")
        return jsonify({"success": False, "message": "创建失败"}), 500


@bp.route("/<int:motto_id>", methods=["PUT"])
@jwt_required()
def update_motto(motto_id):
    """更新座右铭"""
    current_user_id = get_jwt_identity()
    motto = Motto.query.filter_by(id=motto_id, user_id=current_user_id).first()

    if not motto:
        return jsonify({"success": False, "message": "座右铭不存在"}), 404

    data = request.get_json()

    if "content" not in data:
        return jsonify({"success": False, "message": "内容为必填项"}), 400

    try:
        motto.content = data["content"]
        db.session.commit()

        return jsonify(
            {"success": True, "message": "座右铭更新成功", "motto": motto.to_dict()}
        ), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Motto update error: {e}")
        return jsonify({"success": False, "message": "更新失败"}), 500


@bp.route("/<int:motto_id>", methods=["DELETE"])
@jwt_required()
def delete_motto(motto_id):
    """删除座右铭"""
    current_user_id = get_jwt_identity()
    motto = Motto.query.filter_by(id=motto_id, user_id=current_user_id).first()

    if not motto:
        return jsonify({"success": False, "message": "座右铭不存在"}), 404

    try:
        db.session.delete(motto)
        db.session.commit()

        return jsonify({"success": True, "message": "座右铭已删除"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Motto deletion error: {e}")
        return jsonify({"success": False, "message": "删除失败"}), 500
