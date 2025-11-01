"""
Todo API蓝图
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import Todo

bp = Blueprint("todos", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def get_todos():
    """获取所有待办事项"""
    current_user_id = get_jwt_identity()

    status = request.args.get("status")  # 'completed', 'active', 'all'

    query = Todo.query.filter_by(user_id=current_user_id)

    if status == "completed":
        query = query.filter_by(is_completed=True)
    elif status == "active":
        query = query.filter_by(is_completed=False)

    todos = query.order_by(Todo.priority.asc(), Todo.created_at.desc()).all()

    return jsonify({"success": True, "todos": [todo.to_dict() for todo in todos]}), 200


@bp.route("/<int:todo_id>", methods=["GET"])
@jwt_required()
def get_todo(todo_id):
    """获取单个待办事项"""
    current_user_id = get_jwt_identity()
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user_id).first()

    if not todo:
        return jsonify({"success": False, "message": "待办事项不存在"}), 404

    return jsonify({"success": True, "todo": todo.to_dict()}), 200


@bp.route("", methods=["POST"])
@jwt_required()
def create_todo():
    """创建待办事项"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get("content"):
        return jsonify({"success": False, "message": "内容为必填项"}), 400

    try:
        todo = Todo(
            content=data["content"],
            due_date=datetime.fromisoformat(data["due_date"]).date()
            if data.get("due_date")
            else None,
            priority=data.get("priority", 2),
            user_id=current_user_id,
        )
        db.session.add(todo)
        db.session.commit()

        return jsonify(
            {"success": True, "message": "待办事项创建成功", "todo": todo.to_dict()}
        ), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Todo creation error: {e}")
        return jsonify({"success": False, "message": "创建失败"}), 500


@bp.route("/<int:todo_id>", methods=["PUT"])
@jwt_required()
def update_todo(todo_id):
    """更新待办事项"""
    current_user_id = get_jwt_identity()
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user_id).first()

    if not todo:
        return jsonify({"success": False, "message": "待办事项不存在"}), 404

    data = request.get_json()

    try:
        if "content" in data:
            todo.content = data["content"]
        if "due_date" in data:
            todo.due_date = (
                datetime.fromisoformat(data["due_date"]).date()
                if data["due_date"]
                else None
            )
        if "priority" in data:
            todo.priority = data["priority"]
        if "is_completed" in data:
            todo.is_completed = data["is_completed"]
            if data["is_completed"]:
                todo.completed_at = datetime.utcnow()
            else:
                todo.completed_at = None

        db.session.commit()

        return jsonify(
            {"success": True, "message": "待办事项更新成功", "todo": todo.to_dict()}
        ), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Todo update error: {e}")
        return jsonify({"success": False, "message": "更新失败"}), 500


@bp.route("/<int:todo_id>/toggle", methods=["POST"])
@jwt_required()
def toggle_todo(todo_id):
    """切换待办事项完成状态"""
    current_user_id = get_jwt_identity()
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user_id).first()

    if not todo:
        return jsonify({"success": False, "message": "待办事项不存在"}), 404

    try:
        todo.is_completed = not todo.is_completed
        if todo.is_completed:
            todo.completed_at = datetime.utcnow()
        else:
            todo.completed_at = None

        db.session.commit()

        return jsonify(
            {"success": True, "message": "状态更新成功", "todo": todo.to_dict()}
        ), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Todo toggle error: {e}")
        return jsonify({"success": False, "message": "更新失败"}), 500


@bp.route("/<int:todo_id>", methods=["DELETE"])
@jwt_required()
def delete_todo(todo_id):
    """删除待办事项"""
    current_user_id = get_jwt_identity()
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user_id).first()

    if not todo:
        return jsonify({"success": False, "message": "待办事项不存在"}), 404

    try:
        db.session.delete(todo)
        db.session.commit()

        return jsonify({"success": True, "message": "待办事项已删除"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Todo deletion error: {e}")
        return jsonify({"success": False, "message": "删除失败"}), 500
