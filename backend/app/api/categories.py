"""
分类API蓝图
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Category, SubCategory

bp = Blueprint("categories", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def get_categories():
    """获取所有分类"""
    current_user_id = get_jwt_identity()
    include_subs = request.args.get("include_subcategories", "false").lower() == "true"

    categories = (
        Category.query.filter_by(user_id=current_user_id).order_by(Category.name).all()
    )

    current_app.logger.info(
        f"Found {len(categories)} categories for user {current_user_id}"
    )
    for cat in categories:
        current_app.logger.info(f"Category: {cat.name}, id: {cat.id}")

    result = {
        "success": True,
        "categories": [
            cat.to_dict(include_subcategories=include_subs) for cat in categories
        ],
    }
    current_app.logger.info(f"Returning: {result}")

    return jsonify(result), 200


@bp.route("/<int:category_id>", methods=["GET"])
@jwt_required()
def get_category(category_id):
    """获取单个分类"""
    current_user_id = get_jwt_identity()
    category = Category.query.filter_by(id=category_id, user_id=current_user_id).first()

    if not category:
        return jsonify({"success": False, "message": "分类不存在"}), 404

    return jsonify(
        {"success": True, "category": category.to_dict(include_subcategories=True)}
    ), 200


@bp.route("", methods=["POST"])
@jwt_required()
def create_category():
    """创建分类"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    current_app.logger.info(f"Creating category for user {current_user_id}: {data}")

    if not data or not data.get("name"):
        return jsonify({"success": False, "message": "分类名称为必填项"}), 400

    try:
        category = Category(name=data["name"], user_id=current_user_id)
        db.session.add(category)
        db.session.commit()

        current_app.logger.info(
            f"Category created: id={category.id}, name={category.name}"
        )

        return jsonify(
            {"success": True, "message": "分类创建成功", "category": category.to_dict()}
        ), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Category creation error: {e}")
        return jsonify({"success": False, "message": "创建失败"}), 500


@bp.route("/<int:category_id>", methods=["PUT"])
@jwt_required()
def update_category(category_id):
    """更新分类"""
    current_user_id = get_jwt_identity()
    category = Category.query.filter_by(id=category_id, user_id=current_user_id).first()

    if not category:
        return jsonify({"success": False, "message": "分类不存在"}), 404

    data = request.get_json()

    try:
        if "name" in data:
            category.name = data["name"]
        db.session.commit()

        return jsonify(
            {"success": True, "message": "分类更新成功", "category": category.to_dict()}
        ), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Category update error: {e}")
        return jsonify({"success": False, "message": "更新失败"}), 500


@bp.route("/<int:category_id>", methods=["DELETE"])
@jwt_required()
def delete_category(category_id):
    """删除分类"""
    current_user_id = get_jwt_identity()
    category = Category.query.filter_by(id=category_id, user_id=current_user_id).first()

    if not category:
        return jsonify({"success": False, "message": "分类不存在"}), 404

    # 检查是否有子分类
    if category.subcategories.count() > 0:
        return jsonify(
            {"success": False, "message": "无法删除，请先移除此分类下的所有标签"}
        ), 400

    try:
        db.session.delete(category)
        db.session.commit()

        return jsonify({"success": True, "message": "分类已删除"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Category deletion error: {e}")
        return jsonify({"success": False, "message": "删除失败"}), 500


# 子分类路由
@bp.route("/<int:category_id>/subcategories", methods=["POST"])
@jwt_required()
def create_subcategory(category_id):
    """创建子分类"""
    current_user_id = get_jwt_identity()
    category = Category.query.filter_by(id=category_id, user_id=current_user_id).first()

    if not category:
        return jsonify({"success": False, "message": "分类不存在"}), 404

    data = request.get_json()

    if not data or not data.get("name"):
        return jsonify({"success": False, "message": "子分类名称为必填项"}), 400

    try:
        subcategory = SubCategory(name=data["name"], category_id=category_id)
        db.session.add(subcategory)
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "子分类创建成功",
                "subcategory": subcategory.to_dict(),
            }
        ), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Subcategory creation error: {e}")
        return jsonify({"success": False, "message": "创建失败"}), 500


@bp.route("/subcategories/<int:subcategory_id>", methods=["PUT"])
@jwt_required()
def update_subcategory(subcategory_id):
    """更新子分类"""
    current_user_id = get_jwt_identity()
    subcategory = (
        SubCategory.query.join(Category)
        .filter(SubCategory.id == subcategory_id, Category.user_id == current_user_id)
        .first()
    )

    if not subcategory:
        return jsonify({"success": False, "message": "子分类不存在"}), 404

    data = request.get_json()

    try:
        if "name" in data:
            subcategory.name = data["name"]
        if "category_id" in data:
            # 验证新的父分类是否存在且属于当前用户
            new_category = Category.query.filter_by(
                id=data["category_id"], user_id=current_user_id
            ).first()
            if not new_category:
                return jsonify({"success": False, "message": "无效的分类选择"}), 400
            subcategory.category_id = data["category_id"]

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "子分类更新成功",
                "subcategory": subcategory.to_dict(),
            }
        ), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Subcategory update error: {e}")
        return jsonify({"success": False, "message": "更新失败"}), 500


@bp.route("/subcategories/<int:subcategory_id>", methods=["DELETE"])
@jwt_required()
def delete_subcategory(subcategory_id):
    """删除子分类"""
    current_user_id = get_jwt_identity()
    subcategory = (
        SubCategory.query.join(Category)
        .filter(SubCategory.id == subcategory_id, Category.user_id == current_user_id)
        .first()
    )

    if not subcategory:
        return jsonify({"success": False, "message": "子分类不存在"}), 404

    # 检查是否有关联的学习记录
    if subcategory.log_entries.count() > 0:
        return jsonify(
            {
                "success": False,
                "message": f'无法删除标签 "{subcategory.name}"，因为它已关联了学习记录',
            }
        ), 400

    try:
        db.session.delete(subcategory)
        db.session.commit()

        return jsonify({"success": True, "message": "子分类已删除"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Subcategory deletion error: {e}")
        return jsonify({"success": False, "message": "删除失败"}), 500
