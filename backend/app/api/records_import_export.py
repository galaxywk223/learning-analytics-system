"""
数据导入导出相关的API路由
"""

from flask import Blueprint, request, jsonify, current_app, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User
from app.services import data_service

# 创建子蓝图
import_export_bp = Blueprint("import_export", __name__)


@import_export_bp.route("/import", methods=["POST"])
@import_export_bp.route("/import_zip", methods=["POST"])  # legacy compatibility
@jwt_required()
def import_zip():
    """
    与旧项目行为一致：接收一个 zip 文件（字段名 'file'，multipart/form-data），
    调用数据服务导入，为当前登录用户覆盖导入全部数据。
    """
    current_user_id = get_jwt_identity()

    # 1) 取文件
    file_storage = request.files.get("file")
    if not file_storage or not file_storage.filename.lower().endswith(".zip"):
        return jsonify(
            {"success": False, "message": "请上传 .zip 文件（字段名 file）"}
        ), 400

    # 2) 获取用户对象（旧服务签名是 (user, zip_stream)）
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"success": False, "message": "用户不存在"}), 404

    # 3) 调用服务执行导入
    ok, msg = data_service.import_data_for_user(user, file_storage.stream)
    if ok:
        # 与旧项目一致：全量重算效率
        try:
            from app.services.record_service import recalculate_efficiency_for_stage

            stages = user.stages
            for stage in stages:
                recalculate_efficiency_for_stage(stage.id)
        except Exception as e:
            current_app.logger.error(f"重算效率失败: {e}")
            # 不阻止导入成功的响应，仅记录错误

        return jsonify({"success": True, "message": msg or "导入成功"}), 200
    else:
        return jsonify({"success": False, "message": msg or "导入失败"}), 400


@import_export_bp.route("/export", methods=["GET"])
@jwt_required()
def export_zip():
    """
    导出当前用户的全部数据为 zip 文件，与旧项目行为一致。
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"success": False, "message": "用户不存在"}), 404

    try:
        # 调用服务生成 zip 文件内容（字节流）
        success, buffer, filename = data_service.export_data_for_user(user)
        if not success or not buffer:
            return jsonify({"success": False, "message": "导出失败，无数据"}), 400

        # 返回文件下载响应
        return Response(
            buffer.getvalue(),
            mimetype="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename or 'learning_data.zip'}"
            },
        )
    except Exception as e:
        current_app.logger.error(f"Export error: {e}")
        return jsonify({"success": False, "message": f"导出异常: {e}"}), 500


@import_export_bp.route("/clear", methods=["DELETE"])
@import_export_bp.route("/clear_data", methods=["POST"])  # legacy compatibility
@jwt_required()
def clear_data():
    """
    清空当前用户的全部数据，兼容旧项目的两种路由。
    """
    try:
        current_user_id = get_jwt_identity()

        # 获取用户对象
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404

        # 在兼容路径下直接清除，不需要 confirm 参数
        ok, msg = data_service.clear_all_user_data(user)
        if ok:
            return jsonify({"success": True, "message": msg or "数据已清空"}), 200
        return jsonify({"success": False, "message": msg or "清空失败"}), 500
    except Exception as e:
        current_app.logger.error(f"Clear data error: {e}")
        return jsonify({"success": False, "message": f"清空异常: {e}"}), 500
