"""
认证API蓝图
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from app import db
from app.models import User, Motto

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["POST"])
def register():
    """
    用户注册
    ---
    POST /api/auth/register
    Body: {
        "username": "string",
        "email": "string",
        "password": "string"
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "请提供注册信息"}), 400

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    # 验证必填字段
    if not username or not email or not password:
        return jsonify({"success": False, "message": "用户名、邮箱和密码为必填项"}), 400

    # 检查用户是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({"success": False, "message": "用户名已被使用"}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "message": "邮箱已被注册"}), 409

    try:
        # 创建新用户
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        # 为新用户添加预设座右铭
        PRESET_MOTTOS = [
            "书山有路勤为径,学海无涯苦作舟。",
            "业精于勤,荒于嬉;行成于思,毁于随。",
            "不积跬步,无以至千里;不积小流,无以成江海。",
            "少壮不努力,老大徒伤悲。",
            "吾生也有涯,而知也无涯。",
            "天行健,君子以自强不息。",
            "明日复明日,明日何其多。我生待明日,万事成蹉跎。",
        ]
        for content in PRESET_MOTTOS:
            motto = Motto(content=content, user_id=user.id)
            db.session.add(motto)

        db.session.commit()

        current_app.logger.info(f"New user registered: {username}")

        return jsonify(
            {"success": True, "message": "注册成功!", "user": user.to_dict()}
        ), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {e}")
        return jsonify({"success": False, "message": "注册失败,请稍后重试"}), 500


@bp.route("/login", methods=["POST"])
def login():
    """
    用户登录
    ---
    POST /api/auth/login
    Body: {
        "email": "string",
        "password": "string"
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "请提供登录信息"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"success": False, "message": "邮箱和密码为必填项"}), 400

    # 查找用户
    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"success": False, "message": "邮箱或密码错误"}), 401

    # 生成JWT token
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    current_app.logger.info(f"User logged in: {user.username}")

    return jsonify(
        {
            "success": True,
            "message": "登录成功!",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_dict(),
        }
    ), 200


@bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """
    刷新访问令牌
    ---
    POST /api/auth/refresh
    Headers: Authorization: Bearer <refresh_token>
    """
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user_id)

    return jsonify({"success": True, "access_token": new_access_token}), 200


@bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """
    获取当前用户信息
    ---
    GET /api/auth/me
    Headers: Authorization: Bearer <access_token>
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"success": False, "message": "用户不存在"}), 404

    return jsonify({"success": True, "user": user.to_dict()}), 200


@bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    """
    修改密码
    ---
    POST /api/auth/change-password
    Headers: Authorization: Bearer <access_token>
    Body: {
        "current_password": "string",
        "new_password": "string"
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"success": False, "message": "用户不存在"}), 404

    data = request.get_json()
    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if not current_password or not new_password:
        return jsonify({"success": False, "message": "当前密码和新密码为必填项"}), 400

    if not user.check_password(current_password):
        return jsonify({"success": False, "message": "当前密码错误"}), 401

    try:
        user.set_password(new_password)
        db.session.commit()

        current_app.logger.info(f"User changed password: {user.username}")

        return jsonify({"success": True, "message": "密码修改成功!"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Password change error: {e}")
        return jsonify({"success": False, "message": "密码修改失败"}), 500
