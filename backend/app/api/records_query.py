"""
记录查询和统计相关的API路由
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from app.models import LogEntry, Stage
from app.services import record_service

# 创建子蓝图
query_bp = Blueprint("records_query", __name__)


@query_bp.route("/structured", methods=["GET"])
@jwt_required()
def get_structured_records():
    """返回按阶段->周->日分组的结构化学习记录数据 - 与旧项目完全一致

    Query Params:
      stage_id (int, required)
      sort (str, optional) 'desc' or 'asc' 按日期排序方向 (默认 desc)
    """
    current_user_id = get_jwt_identity()
    stage_id = request.args.get("stage_id", type=int)
    if not stage_id:
        return jsonify({"success": False, "message": "请指定阶段ID"}), 400

    stage = Stage.query.filter_by(id=stage_id, user_id=current_user_id).first()
    if not stage:
        return jsonify({"success": False, "message": "阶段不存在"}), 404

    sort_order = request.args.get("sort", "desc")

    # 使用旧项目的服务层方法
    structured_logs = record_service.get_structured_logs_for_stage(stage, sort_order)

    # 为每一天计算总时长（前端需要）
    for week_data in structured_logs:
        for day_data in week_data["days"]:
            total_duration = sum(
                log.get("actual_duration", 0) or 0 for log in day_data["logs"]
            )
            day_data["total_duration"] = total_duration

    return jsonify({"success": True, "data": structured_logs, "stage_name": stage.name})


@query_bp.route("/list", methods=["GET"])
@jwt_required()
def list_records():
    """获取记录列表 - 支持分页和筛选"""
    current_user_id = get_jwt_identity()

    # 获取查询参数
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    stage_id = request.args.get("stage_id", type=int)
    category_id = request.args.get("category_id", type=int)
    subcategory_id = request.args.get("subcategory_id", type=int)
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    try:
        # 构建查询
        query = LogEntry.query.join(Stage).filter(Stage.user_id == current_user_id)

        # 应用筛选条件
        if stage_id:
            query = query.filter_by(stage_id=stage_id)

        if subcategory_id:
            query = query.filter_by(subcategory_id=subcategory_id)
        elif category_id:
            # 通过子分类关联过滤分类
            query = query.join(LogEntry.subcategory).filter(
                LogEntry.subcategory.has(category_id=category_id)
            )

        # 日期范围筛选
        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(LogEntry.log_date >= start_date_obj)

        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(LogEntry.log_date <= end_date_obj)

        # 按日期降序排列
        query = query.order_by(LogEntry.log_date.desc(), LogEntry.id.desc())

        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        # 格式化结果
        records = [
            record_service.format_record_for_response(record)
            for record in pagination.items
        ]

        return jsonify(
            {
                "success": True,
                "data": {
                    "records": records,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": pagination.total,
                        "pages": pagination.pages,
                        "has_prev": pagination.has_prev,
                        "has_next": pagination.has_next,
                    },
                },
            }
        )

    except Exception as e:
        current_app.logger.error(f"List records error: {e}")
        return jsonify(
            {"success": False, "message": f"获取记录列表失败: {str(e)}"}
        ), 500


@query_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_record_stats():
    """获取记录统计信息"""
    current_user_id = get_jwt_identity()

    # 获取查询参数
    stage_id = request.args.get("stage_id", type=int)
    days = request.args.get("days", 30, type=int)

    try:
        # 构建基础查询
        query = LogEntry.query.join(Stage).filter(Stage.user_id == current_user_id)

        if stage_id:
            query = query.filter_by(stage_id=stage_id)

        # 时间范围（最近N天）
        if days > 0:
            start_date = (datetime.now() - timedelta(days=days)).date()
            query = query.filter(LogEntry.log_date >= start_date)

        records = query.all()

        # 计算统计信息
        stats = record_service.calculate_record_statistics(records)

        return jsonify({"success": True, "data": stats})

    except Exception as e:
        current_app.logger.error(f"Get record stats error: {e}")
        return jsonify(
            {"success": False, "message": f"获取统计信息失败: {str(e)}"}
        ), 500


@query_bp.route("/recent", methods=["GET"])
@jwt_required()
def get_recent_records():
    """获取最近的记录"""
    current_user_id = get_jwt_identity()

    limit = min(request.args.get("limit", 10, type=int), 50)

    try:
        records = (
            LogEntry.query.join(Stage)
            .filter(Stage.user_id == current_user_id)
            .order_by(LogEntry.created_at.desc())
            .limit(limit)
            .all()
        )

        formatted_records = [
            record_service.format_record_for_response(record) for record in records
        ]

        return jsonify({"success": True, "data": formatted_records})

    except Exception as e:
        current_app.logger.error(f"Get recent records error: {e}")
        return jsonify(
            {"success": False, "message": f"获取最近记录失败: {str(e)}"}
        ), 500
