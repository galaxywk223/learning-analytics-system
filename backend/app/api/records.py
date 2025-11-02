"""
学习记录API蓝图 - 重构版本

将原本626行的大文件拆分为多个功能模块：
- records_import_export.py: 数据导入导出功能
- records_crud.py: 记录的增删改查功能
- records_query.py: 记录查询和统计功能
"""

from flask import Blueprint
from .records_import_export import import_export_bp
from .records_crud import crud_bp
from .records_query import query_bp

# 创建主蓝图
bp = Blueprint("records", __name__)

# 注册子蓝图
bp.register_blueprint(import_export_bp, url_prefix="")
bp.register_blueprint(crud_bp, url_prefix="")
bp.register_blueprint(query_bp, url_prefix="")


# 兼容性路由 - 保持与原API的兼容性
@bp.route("/health", methods=["GET"])
def health_check():
    """健康检查接口"""
    return {"status": "ok", "service": "records", "version": "2.0"}
