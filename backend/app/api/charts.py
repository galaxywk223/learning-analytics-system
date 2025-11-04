"""
图表统计API蓝图
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Stage
from app.services.chart_service import get_chart_data_for_user, get_category_chart_data
from app.services.chart_plotter import export_trends_image, export_category_image
import zipfile
import io

bp = Blueprint("charts", __name__)


@bp.route("/overview", methods=["GET"])
@jwt_required()
def get_overview():
    """
    获取概览统计数据（趋势分析）
    包含KPIs、每周/每日时长趋势、效率趋势、阶段注释等
    完全匹配旧项目 /charts/api/data 的返回格式
    """
    current_user_id = get_jwt_identity()

    try:
        # 获取图表数据
        chart_data = get_chart_data_for_user(current_user_id)

        # 格式化 avg_daily_minutes 为可读格式
        if chart_data.get("kpis") and "avg_daily_minutes" in chart_data["kpis"]:
            raw_minutes = chart_data["kpis"]["avg_daily_minutes"]
            hours, minutes = divmod(int(raw_minutes or 0), 60)
            chart_data["kpis"]["avg_daily_formatted"] = f"{hours}小时 {minutes}分钟"

        # 直接返回chart_data（不包装在data字段中，与旧项目一致）
        return jsonify(chart_data), 200

    except Exception as e:
        current_app.logger.error(f"Error getting chart overview: {e}", exc_info=True)
        return jsonify({"success": False, "message": "获取图表数据失败"}), 500


@bp.route("/categories", methods=["GET"])
@jwt_required()
def get_categories():
    """
    获取分类统计数据（分类占比）
    支持按阶段过滤
    返回格式与旧项目 /category_charts/api/data 一致
    """
    current_user_id = get_jwt_identity()
    stage_id = request.args.get("stage_id")
    range_mode = request.args.get("range_mode", "all")
    start_date_raw = request.args.get("start_date")
    end_date_raw = request.args.get("end_date")

    def _parse_date(value):
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return None

    parsed_start = _parse_date(start_date_raw)
    parsed_end = _parse_date(end_date_raw)

    if range_mode in {"daily", "weekly", "monthly", "custom"}:
        if not parsed_start or not parsed_end or parsed_start > parsed_end:
            return jsonify({"success": False, "message": "无效的时间范围"}), 400

    try:
        # 处理stage_id参数
        if stage_id and stage_id != "all" and stage_id.isdigit():
            stage_id = int(stage_id)
            # 验证阶段所有权
            stage = Stage.query.filter_by(id=stage_id, user_id=current_user_id).first()
            if not stage:
                return jsonify({"success": False, "message": "阶段不存在"}), 404
        else:
            stage_id = None

        # 获取分类图表数据
        category_data = get_category_chart_data(
            current_user_id,
            stage_id=stage_id,
            start_date=parsed_start,
            end_date=parsed_end,
        )

        if category_data is None:
            # 返回空数据结构，与旧项目一致
            return jsonify({"main": {"labels": [], "data": []}, "drilldown": {}}), 200

        # 直接返回数据，与旧项目格式一致
        return jsonify(category_data), 200

    except Exception as e:
        current_app.logger.error(f"Error getting category charts: {e}", exc_info=True)
        return jsonify({"success": False, "message": "获取分类数据失败"}), 500


@bp.route("/stages", methods=["GET"])
@jwt_required()
def get_stages_list():
    """
    获取用户的所有阶段列表(用于图表页面的阶段选择器)
    """
    current_user_id = get_jwt_identity()

    try:
        stages = (
            Stage.query.filter_by(user_id=current_user_id)
            .order_by(Stage.start_date.desc())
            .all()
        )

        return jsonify(
            {"success": True, "data": {"stages": [stage.to_dict() for stage in stages]}}
        ), 200

    except Exception as e:
        current_app.logger.error(f"Error getting stages list: {e}", exc_info=True)
        return jsonify({"success": False, "message": "获取阶段列表失败"}), 500


@bp.route("/export", methods=["GET"])
@jwt_required()
def export_charts():
    """
    导出图表为ZIP文件
    包含趋势图和分类图
    """
    current_user_id = get_jwt_identity()

    try:
        from app.models import User

        user = User.query.get(current_user_id)
        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404

        # 获取图表数据
        trend_data = get_chart_data_for_user(current_user_id)
        category_data = get_category_chart_data(current_user_id, stage_id=None)

        # 生成图表图片
        trends_img = None
        category_img = None

        if trend_data and trend_data.get("has_data"):
            trends_img = export_trends_image(user.username, trend_data)

        if category_data:
            category_img = export_category_image(user.username, category_data)

        # 创建ZIP文件 (旧版命名规范: trends_summary.png / category_summary.png)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            if trends_img:
                zip_file.writestr("trends_summary.png", trends_img.getvalue())
            if category_img:
                zip_file.writestr("category_summary.png", category_img.getvalue())

        zip_buffer.seek(0)

        # 旧版文件名格式: {username}_charts_YYYY-MM-DD.zip
        from datetime import date

        safe_username = user.username.replace(" ", "_") if user.username else "user"
        today_str = date.today().strftime("%Y-%m-%d")
        download_name = f"{safe_username}_charts_{today_str}.zip"

        return Response(
            zip_buffer.getvalue(),
            mimetype="application/zip",
            headers={"Content-Disposition": f"attachment; filename={download_name}"},
        )

    except Exception as e:
        current_app.logger.error(f"Error exporting charts: {e}", exc_info=True)
        return jsonify({"success": False, "message": "导出图表失败"}), 500
