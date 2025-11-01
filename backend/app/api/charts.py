"""
图表统计API蓝图
"""

from flask import Blueprint, request, jsonify, current_app, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Stage
from app.services.chart_service import get_chart_data_for_user, get_category_chart_data
from app.services.wordcloud_service import generate_wordcloud_for_user
from app.services.chart_plotter import export_trends_image, export_category_image
import zipfile
import io

bp = Blueprint("charts", __name__)

# 可用于前端展示的词云遮罩与调色板选项
WORDCLOUD_MASK_OPTIONS = [
    {"file": "random", "name": "随机形状"},
    {"file": "brain-profile.png", "name": "大脑"},
    {"file": "book-open.png", "name": "书本"},
    {"file": "lightbulb-on.png", "name": "灯泡"},
    {"file": "graduation-cap.png", "name": "毕业帽"},
    {"file": "trophy-solid.png", "name": "奖杯"},
    {"file": "tree-of-knowledge.png", "name": "知识树"},
    {"file": "arrow-growth.png", "name": "成长箭头"},
    {"file": "key-solid.png", "name": "智慧之钥"},
    {"file": "puzzle-piece.png", "name": "知识拼图"},
    {"file": "dialogue-bubble.png", "name": "思维气泡"},
    {"file": "laptop-solid.png", "name": "电脑"},
    {"file": "code-brackets.png", "name": "代码"},
    {"file": "gear-solid.png", "name": "齿轮"},
    {"file": "flask-solid.png", "name": "烧瓶"},
    {"file": "microscope.png", "name": "显微镜"},
    {"file": "bar-chart.png", "name": "图表"},
]

WORDCLOUD_PALETTES = [
    {"name": "default", "label": "默认"},
    {"name": "warm", "label": "暖色"},
    {"name": "cool", "label": "冷色"},
    {"name": "vibrant", "label": "鲜艳"},
    {"name": "mono", "label": "单色"},
]


@bp.route("/wordcloud/options", methods=["GET"])
@jwt_required()
def wordcloud_options():
    """返回词云遮罩与调色板可选项供前端渲染选择器"""
    return jsonify(
        {
            "success": True,
            "masks": WORDCLOUD_MASK_OPTIONS,
            "palettes": WORDCLOUD_PALETTES,
        }
    ), 200


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
        category_data = get_category_chart_data(current_user_id, stage_id)

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


@bp.route("/wordcloud", methods=["GET"])
@jwt_required()
def get_wordcloud():
    """
    生成并返回词云图片
    查询参数:
    - stage_id: 阶段ID (可选, 'all'或具体ID)
    - mask: 遮罩图片名称 (可选, 默认'random')
    - palette: 调色板名称 (可选, 默认'default')

    返回204状态码表示无数据
    """
    current_user_id = get_jwt_identity()

    stage_id = request.args.get("stage_id")
    mask_name = request.args.get("mask", "random")
    palette = request.args.get("palette", "default")

    try:
        # 处理stage_id参数
        if stage_id and stage_id != "all" and stage_id.isdigit():
            stage = Stage.query.filter_by(
                id=int(stage_id), user_id=current_user_id
            ).first()
            if not stage:
                return jsonify({"success": False, "message": "阶段不存在"}), 404
            stage_id = int(stage_id)
        else:
            stage_id = None

        # 生成词云
        img_buffer = generate_wordcloud_for_user(
            current_user_id, stage_id=stage_id, mask_name=mask_name, palette=palette
        )

        if img_buffer:
            return Response(
                img_buffer.getvalue(),
                mimetype="image/png",
                headers={"Content-Type": "image/png"},
            )
        else:
            # 返回204 No Content，与旧项目一致
            return "", 204

    except Exception as e:
        current_app.logger.error(f"Error generating wordcloud: {e}", exc_info=True)
        return jsonify({"success": False, "message": "生成词云失败"}), 500


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
