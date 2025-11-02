"""
里程碑API蓝图
"""

import os
from flask import Blueprint, request, jsonify, current_app
from flask import send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from werkzeug.utils import secure_filename
from app import db
from app.models import Milestone, MilestoneCategory, MilestoneAttachment

bp = Blueprint("milestones", __name__)

ALLOWED_ATTACHMENT_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "pdf",
    "doc",
    "docx",
    "txt",
}


def allowed_file(filename, allowed_extensions):
    """检查文件扩展名是否允许"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


@bp.route("", methods=["GET"])
@jwt_required()
def get_milestones():
    """获取里程碑列表（支持分页与分类筛选）"""
    current_user_id = get_jwt_identity()

    category_id = request.args.get("category_id", type=int)
    page = request.args.get("page", type=int)
    per_page = request.args.get("per_page", type=int)

    query = Milestone.query.filter_by(user_id=current_user_id)
    if category_id:
        query = query.filter_by(category_id=category_id)

    # 按旧项目排序：事件日期倒序，其次ID倒序
    query = query.order_by(Milestone.event_date.desc(), Milestone.id.desc())

    # 如果未提供分页参数，保持旧行为：返回全部列表（用于兼容现有前端）
    if not page and not per_page:
        milestones = query.all()
        return jsonify(
            {
                "success": True,
                "milestones": [m.to_dict(include_attachments=True) for m in milestones],
                "pagination": None,
            }
        ), 200

    # 处理分页（默认每页10条）
    page = page or 1
    per_page = per_page or 10
    pagination_obj = query.paginate(page=page, per_page=per_page, error_out=False)
    items = [m.to_dict(include_attachments=True) for m in pagination_obj.items]

    return jsonify(
        {
            "success": True,
            "milestones": items,  # 保持键名"milestones"以兼容现有代码
            "pagination": {
                "page": pagination_obj.page,
                "per_page": pagination_obj.per_page,
                "total": pagination_obj.total,
                "pages": pagination_obj.pages,
                "has_next": pagination_obj.has_next,
                "has_prev": pagination_obj.has_prev,
            },
        }
    ), 200


@bp.route("/<int:milestone_id>", methods=["GET"])
@jwt_required()
def get_milestone(milestone_id):
    """获取单个里程碑"""
    current_user_id = get_jwt_identity()
    current_app.logger.info(
        f"[获取里程碑] 用户 {current_user_id} 请求获取里程碑 {milestone_id}"
    )

    milestone = Milestone.query.filter_by(
        id=milestone_id, user_id=current_user_id
    ).first()

    if not milestone:
        current_app.logger.warning(
            f"[获取里程碑] 里程碑 {milestone_id} 不存在或不属于用户 {current_user_id}"
        )
        return jsonify({"success": False, "message": "里程碑不存在"}), 404

    milestone_data = milestone.to_dict(include_attachments=True)
    current_app.logger.info(
        f"[获取里程碑] 返回数据，附件数量: {len(milestone_data.get('attachments', []))}"
    )

    return jsonify({"success": True, "milestone": milestone_data}), 200


@bp.route("", methods=["POST"])
@jwt_required()
def create_milestone():
    """创建里程碑"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get("title"):
        return jsonify({"success": False, "message": "标题为必填项"}), 400

    try:
        milestone = Milestone(
            title=data["title"],
            event_date=datetime.fromisoformat(data["event_date"]).date()
            if data.get("event_date")
            else datetime.now().date(),
            description=data.get("description"),
            category_id=data.get("category_id"),
            user_id=current_user_id,
        )
        db.session.add(milestone)
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "里程碑创建成功",
                "milestone": milestone.to_dict(include_attachments=True),
            }
        ), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Milestone creation error: {e}")
        return jsonify({"success": False, "message": "创建失败"}), 500


@bp.route("/<int:milestone_id>", methods=["PUT"])
@jwt_required()
def update_milestone(milestone_id):
    """更新里程碑"""
    current_user_id = get_jwt_identity()
    milestone = Milestone.query.filter_by(
        id=milestone_id, user_id=current_user_id
    ).first()

    if not milestone:
        return jsonify({"success": False, "message": "里程碑不存在"}), 404

    data = request.get_json()

    try:
        if "title" in data:
            milestone.title = data["title"]
        if "event_date" in data:
            milestone.event_date = datetime.fromisoformat(data["event_date"]).date()
        if "description" in data:
            milestone.description = data["description"]
        if "category_id" in data:
            milestone.category_id = data["category_id"]

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "里程碑更新成功",
                "milestone": milestone.to_dict(include_attachments=True),
            }
        ), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Milestone update error: {e}")
        return jsonify({"success": False, "message": "更新失败"}), 500


@bp.route("/<int:milestone_id>", methods=["DELETE"])
@jwt_required()
def delete_milestone(milestone_id):
    """删除里程碑"""
    current_user_id = get_jwt_identity()
    milestone = Milestone.query.filter_by(
        id=milestone_id, user_id=current_user_id
    ).first()

    if not milestone:
        return jsonify({"success": False, "message": "里程碑不存在"}), 404

    try:
        db.session.delete(milestone)
        db.session.commit()

        return jsonify({"success": True, "message": "里程碑已删除"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Milestone deletion error: {e}")
        return jsonify({"success": False, "message": "删除失败"}), 500


# 里程碑分类路由
@bp.route("/categories", methods=["GET"])
@jwt_required()
def get_milestone_categories():
    """获取所有里程碑分类"""
    current_user_id = get_jwt_identity()
    categories = MilestoneCategory.query.filter_by(user_id=current_user_id).all()

    return jsonify(
        {"success": True, "categories": [cat.to_dict() for cat in categories]}
    ), 200


@bp.route("/categories", methods=["POST"])
@jwt_required()
def create_milestone_category():
    """创建里程碑分类"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get("name"):
        return jsonify({"success": False, "message": "分类名称为必填项"}), 400

    try:
        category = MilestoneCategory(name=data["name"], user_id=current_user_id)
        db.session.add(category)
        db.session.commit()

        return jsonify(
            {"success": True, "message": "分类创建成功", "category": category.to_dict()}
        ), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Category creation error: {e}")
        return jsonify({"success": False, "message": "创建失败"}), 500


@bp.route("/categories/<int:category_id>", methods=["PUT"])
@jwt_required()
def update_milestone_category(category_id):
    """更新里程碑分类名称"""
    current_user_id = get_jwt_identity()
    category = MilestoneCategory.query.filter_by(
        id=category_id, user_id=current_user_id
    ).first()
    if not category:
        return jsonify({"success": False, "message": "分类不存在"}), 404

    data = request.get_json()
    if not data or not data.get("name") or not str(data.get("name")).strip():
        return jsonify({"success": False, "message": "分类名称不能为空"}), 400

    try:
        category.name = data["name"].strip()
        db.session.commit()
        return jsonify(
            {"success": True, "message": "分类更新成功", "category": category.to_dict()}
        ), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Category update error: {e}")
        return jsonify({"success": False, "message": "更新失败"}), 500


@bp.route("/categories/<int:category_id>", methods=["DELETE"])
@jwt_required()
def delete_milestone_category(category_id):
    """删除里程碑分类（若已关联里程碑则拒绝）"""
    current_user_id = get_jwt_identity()
    category = MilestoneCategory.query.filter_by(
        id=category_id, user_id=current_user_id
    ).first()
    if not category:
        return jsonify({"success": False, "message": "分类不存在"}), 404

    # 检查是否有关联里程碑，保持与旧项目逻辑一致：有里程碑则不可删
    if category.milestones.count() > 0:
        return jsonify(
            {"success": False, "message": "无法删除：该分类下仍有关联里程碑"}
        ), 400

    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify({"success": True, "message": "分类已删除"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Category deletion error: {e}")
        return jsonify({"success": False, "message": "删除失败"}), 500


# 里程碑附件路由
@bp.route("/<int:milestone_id>/attachments", methods=["POST"])
@jwt_required()
def upload_attachment(milestone_id):
    """上传里程碑附件"""
    current_user_id = get_jwt_identity()
    current_app.logger.info(
        f"[上传附件] 用户 {current_user_id} 请求上传附件到里程碑 {milestone_id}"
    )

    # 验证里程碑所有权
    milestone = Milestone.query.filter_by(
        id=milestone_id, user_id=current_user_id
    ).first()
    if not milestone:
        current_app.logger.warning(
            f"[上传附件] 里程碑 {milestone_id} 不存在或不属于用户 {current_user_id}"
        )
        return jsonify({"success": False, "message": "里程碑不存在"}), 404

    if "file" not in request.files:
        current_app.logger.warning(f"[上传附件] 请求中没有文件")
        return jsonify({"success": False, "message": "没有文件被上传"}), 400

    file = request.files["file"]
    current_app.logger.info(f"[上传附件] 接收到文件: {file.filename}")

    if file.filename == "":
        return jsonify({"success": False, "message": "文件名为空"}), 400

    if not allowed_file(file.filename, ALLOWED_ATTACHMENT_EXTENSIONS):
        current_app.logger.warning(f"[上传附件] 不支持的文件格式: {file.filename}")
        return jsonify(
            {
                "success": False,
                "message": "不支持的文件格式,仅支持图片、PDF和文档文件",
            }
        ), 400

    try:
        # 生成安全的文件名
        timestamp = int(datetime.now().timestamp())
        ext = file.filename.rsplit(".", 1)[1].lower()
        original_name = os.path.splitext(file.filename)[0]
        filename = f"milestone_{milestone_id}_{timestamp}.{ext}"
        filename = secure_filename(filename)

        # 确保上传目录存在（使用 UPLOAD_FOLDER）
        upload_folder = current_app.config.get("UPLOAD_FOLDER")
        if not upload_folder:
            current_app.logger.error(f"[上传附件] UPLOAD_FOLDER 未配置")
            return jsonify({"success": False, "message": "上传功能未配置"}), 500

        user_upload_dir = os.path.join(upload_folder, str(current_user_id))
        os.makedirs(user_upload_dir, exist_ok=True)
        current_app.logger.info(f"[上传附件] 上传目录: {user_upload_dir}")

        # 保存文件
        file_path = os.path.join(user_upload_dir, filename)
        file.save(file_path)
        current_app.logger.info(f"[上传附件] 文件已保存到: {file_path}")

        # 创建附件记录
        relative_path = f"{current_user_id}/{filename}"
        attachment = MilestoneAttachment(
            milestone_id=milestone_id,
            file_path=relative_path,
            original_filename=original_name,
        )
        db.session.add(attachment)
        db.session.commit()
        current_app.logger.info(
            f"[上传附件] 附件记录已创建: ID={attachment.id}, 路径={relative_path}"
        )

        return jsonify(
            {
                "success": True,
                "message": "附件上传成功",
                "attachment": attachment.to_dict(),
            }
        ), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[上传附件] 上传失败: {e}", exc_info=True)
        return jsonify({"success": False, "message": f"上传失败: {str(e)}"}), 500


@bp.route("/<int:milestone_id>/attachments/<int:attachment_id>", methods=["DELETE"])
@jwt_required()
def delete_attachment(milestone_id, attachment_id):
    """删除里程碑附件"""
    current_user_id = get_jwt_identity()

    # 验证里程碑所有权
    milestone = Milestone.query.filter_by(
        id=milestone_id, user_id=current_user_id
    ).first()
    if not milestone:
        return jsonify({"success": False, "message": "里程碑不存在"}), 404

    # 获取附件
    attachment = MilestoneAttachment.query.filter_by(
        id=attachment_id, milestone_id=milestone_id
    ).first()
    if not attachment:
        return jsonify({"success": False, "message": "附件不存在"}), 404

    try:
        # 删除文件（使用 UPLOAD_FOLDER）
        upload_folder = current_app.config.get("UPLOAD_FOLDER")
        if upload_folder:
            file_path = os.path.join(upload_folder, attachment.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)

        # 删除数据库记录
        db.session.delete(attachment)
        db.session.commit()

        return jsonify({"success": True, "message": "附件已删除"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Attachment deletion error: {e}")
        return jsonify({"success": False, "message": "删除失败"}), 500


@bp.route("/attachments/<path:filepath>", methods=["GET"])
def download_attachment(filepath):
    """
    下载附件：不需要JWT认证，通过验证附件记录是否存在于数据库来确保安全性。
    filepath 形如 'user_id/filename'
    """
    # 规范路径分隔符
    normalized = filepath.replace("\\", "/")
    parts = normalized.split("/")
    if len(parts) < 2:
        return jsonify({"success": False, "message": "无效的路径"}), 400

    user_part = parts[0]
    filename = parts[-1]

    # 验证该文件路径是否存在于数据库的附件记录中（安全检查）
    attachment = MilestoneAttachment.query.filter_by(file_path=filepath).first()
    if not attachment:
        current_app.logger.warning(f"[下载附件] 附件记录不存在: {filepath}")
        return jsonify({"success": False, "message": "附件不存在或已被删除"}), 404

    # 使用 UPLOAD_FOLDER
    upload_folder = current_app.config.get("UPLOAD_FOLDER")
    if not upload_folder:
        return jsonify({"success": False, "message": "未配置上传目录"}), 500

    user_dir = os.path.join(upload_folder, user_part)
    file_full_path = os.path.join(user_dir, filename)

    if not os.path.exists(file_full_path):
        current_app.logger.warning(f"[下载附件] 文件不存在: {file_full_path}")
        return jsonify({"success": False, "message": "文件不存在"}), 404

    current_app.logger.info(f"[下载附件] 发送文件: {file_full_path}")
    # 发送文件（as_attachment=False 允许在浏览器中直接查看）
    return send_from_directory(user_dir, filename, as_attachment=False)
