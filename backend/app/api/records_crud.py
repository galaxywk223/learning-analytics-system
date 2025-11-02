"""
记录CRUD操作相关的API路由
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import LogEntry, Stage, SubCategory
from app.services import record_service

# 创建子蓝图
crud_bp = Blueprint("records_crud", __name__)


@crud_bp.route("/", methods=["POST"], strict_slashes=False)
@jwt_required()
def create_record():
    """
    创建新的学习记录

    必需字段：
    - task: 任务名称
    - log_date: 日期 (YYYY-MM-DD)
    - subcategory_id: 标签(子分类)ID
    - actual_duration: 实际时长(分钟)

    可选字段：
    - stage_id: 阶段ID (默认使用用户最新阶段)
    - time_slot: 时间段 (如 "09:00-10:30")
    - notes: 笔记
    - mood: 心情 (1-5)
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "无效的JSON数据"}), 400

    try:
        # 验证必需字段
        required_fields = ["task", "subcategory_id", "log_date", "actual_duration"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify(
                {
                    "success": False,
                    "message": f"缺少必需字段: {', '.join(missing_fields)}",
                }
            ), 400

        # 获取或验证阶段
        stage_id = data.get("stage_id")
        if stage_id:
            stage = Stage.query.filter_by(id=stage_id, user_id=current_user_id).first()
            if not stage:
                return jsonify({"success": False, "message": "阶段不存在"}), 404
        else:
            # 如果没有提供stage_id，使用用户最新的阶段
            stage = (
                Stage.query.filter_by(user_id=current_user_id)
                .order_by(Stage.start_date.desc())
                .first()
            )
            if not stage:
                return jsonify({"success": False, "message": "请先创建学习阶段"}), 400
            stage_id = stage.id

        # 验证子分类归属
        subcategory = (
            SubCategory.query.join(SubCategory.category)
            .filter(
                SubCategory.id == data["subcategory_id"],
                SubCategory.category.has(user_id=current_user_id),
            )
            .first()
        )
        if not subcategory:
            return jsonify({"success": False, "message": "标签不存在"}), 404

        # 处理时长 - 转换为小时
        actual_duration = float(data["actual_duration"]) / 60.0
        if actual_duration <= 0:
            return jsonify({"success": False, "message": "时长必须大于0"}), 400

        # 解析日期
        try:
            if isinstance(data["log_date"], str):
                log_date = datetime.strptime(data["log_date"], "%Y-%m-%d").date()
            else:
                log_date = data["log_date"]
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "日期格式错误"}), 400

        # 创建记录 - 只包含必要字段
        record = LogEntry(
            stage_id=stage_id,
            task=data["task"],
            subcategory_id=data["subcategory_id"],
            actual_duration=actual_duration,
            log_date=log_date,
            time_slot=data.get("time_slot", ""),
            notes=data.get("notes", ""),
            mood=data.get("mood"),
            created_at=datetime.utcnow(),
        )

        db.session.add(record)
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "记录创建成功",
                "data": {
                    "id": record.id,
                    "task": record.task,
                    "actual_duration": float(record.actual_duration),
                    "log_date": record.log_date.isoformat(),
                    "time_slot": record.time_slot,
                },
            }
        ), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create record error: {e}")
        return jsonify({"success": False, "message": f"创建记录失败: {str(e)}"}), 500


@crud_bp.route("/<int:record_id>", methods=["GET"])
@jwt_required()
def get_record(record_id):
    """获取单个记录详情"""
    current_user_id = get_jwt_identity()

    record = LogEntry.query.filter_by(id=record_id, user_id=current_user_id).first()

    if not record:
        return jsonify({"success": False, "message": "记录不存在"}), 404

    return jsonify(
        {"success": True, "data": record_service.format_record_for_response(record)}
    )


@crud_bp.route("/<int:record_id>", methods=["PUT"])
@jwt_required()
def update_record(record_id):
    """更新学习记录"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "无效的JSON数据"}), 400

    try:
        # 获取记录
        record = LogEntry.query.filter_by(id=record_id, user_id=current_user_id).first()

        if not record:
            return jsonify({"success": False, "message": "记录不存在"}), 404

        # 保存原阶段ID用于效率重算
        original_stage_id = record.stage_id

        # 更新字段
        updateable_fields = [
            "task",
            "stage_id",
            "subcategory_id",
            "actual_duration",
            "mood",
            "efficiency",
            "method",
            "content",
            "notes",
            "time_slot",
            "log_date",
        ]

        for field in updateable_fields:
            if field in data:
                if field == "log_date":
                    # 处理日期字段
                    if isinstance(data[field], str):
                        setattr(
                            record,
                            field,
                            datetime.strptime(data[field], "%Y-%m-%d").date(),
                        )
                    else:
                        setattr(record, field, data[field])
                else:
                    setattr(record, field, data[field])

        record.updated_at = datetime.utcnow()
        db.session.commit()

        # 重新计算相关阶段效率
        record_service.recalculate_efficiency_for_stage(original_stage_id)
        if record.stage_id != original_stage_id:
            record_service.recalculate_efficiency_for_stage(record.stage_id)

        return jsonify(
            {
                "success": True,
                "message": "记录更新成功",
                "data": record_service.format_record_for_response(record),
            }
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update record error: {e}")
        return jsonify({"success": False, "message": f"更新记录失败: {str(e)}"}), 500


@crud_bp.route("/<int:record_id>", methods=["DELETE"])
@jwt_required()
def delete_record(record_id):
    """删除学习记录"""
    current_user_id = get_jwt_identity()

    try:
        record = LogEntry.query.filter_by(id=record_id, user_id=current_user_id).first()

        if not record:
            return jsonify({"success": False, "message": "记录不存在"}), 404

        stage_id = record.stage_id

        db.session.delete(record)
        db.session.commit()

        # 重新计算阶段效率
        record_service.recalculate_efficiency_for_stage(stage_id)

        return jsonify({"success": True, "message": "记录删除成功"})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete record error: {e}")
        return jsonify({"success": False, "message": f"删除记录失败: {str(e)}"}), 500
