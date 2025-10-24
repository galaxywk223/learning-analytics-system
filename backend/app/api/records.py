"""
学习记录API蓝图
"""

from flask import Blueprint, request, jsonify, current_app, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date
from app import db
from app.models import (
    LogEntry,
    Stage,
    Category,
    SubCategory,
    User,
)
from app.services import data_service, record_service

bp = Blueprint("records", __name__)


@bp.route("/import", methods=["POST"])
@bp.route("/import_zip", methods=["POST"])  # legacy compatibility
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
        # 与旧项目一致：全量重算效率（如你暂不希望重算，可先去掉这一段）
        try:
            # 这里使用旧服务里那套按 stage 重算的方法名；若你放在 record_service，可在此调用
            from app.services.record_service import recalculate_efficiency_for_stage

            stages = Stage.query.filter_by(user_id=user.id).all()
            for s in stages:
                recalculate_efficiency_for_stage(s)
        except Exception as e:
            current_app.logger.warning(f"效率重算失败（已忽略）：{e}")

        return jsonify({"success": True, "message": msg}), 200
    else:
        return jsonify({"success": False, "message": msg}), 500


# ---------------- Legacy compatibility export/clear routes -----------------
@bp.route("/export", methods=["GET"])
@bp.route("/export_zip", methods=["GET"])  # legacy compatibility path
@jwt_required()
def export_zip():
    """Export all user data as a zip archive (legacy path /export_zip supported)."""
    current_user_id = get_jwt_identity()
    try:
        # Use data_service to build the in-memory zip (assumes service provides this)
        ok, stream, filename = data_service.export_data_for_user(current_user_id)
        if not ok:
            return jsonify({"success": False, "message": "导出失败"}), 500
        # Stream response similar to legacy implementation
        from flask import send_file

        return send_file(
            stream,
            mimetype="application/zip",
            as_attachment=True,
            download_name=filename or "records_backup.zip",
        )
    except Exception as e:
        current_app.logger.error(f"Export zip error: {e}")
        return jsonify({"success": False, "message": f"导出异常: {e}"}), 500


@bp.route("/clear_all", methods=["POST"])
@bp.route("/clear_data", methods=["POST"])  # legacy compatibility path
@jwt_required()
def clear_all_data_compat():
    """Clear all user data (legacy path /clear_data supported). Uses compatibility signature without confirm flag."""
    current_user_id = get_jwt_identity()
    try:
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


"""记录相关 API 路由。

注意：原先存在一个简化版快速添加路由 add_record()，字段使用 task,duration,category 等，
但当前数据模型 LogEntry 不再包含 category_id / planned_duration 字段，而是通过 subcategory_id
关联分类并仅存 actual_duration。因此该旧路由与现行模型不兼容，且与 create_record() 冲突
（均使用 POST /api/records）。为避免覆盖和造成前端请求“无反应”，已移除旧的 add_record 路由。
前端统一使用 create_record() 所需的字段：stage_id, task, duration_hours/duration_minutes 或 actual_duration,
subcategory_id, mood, notes, log_date 等。
"""


# ---------------- New structured records endpoint -----------------
@bp.route("/structured", methods=["GET"])
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
    for week in structured_logs:
        for day in week["days"]:
            day["total_duration"] = sum(log.actual_duration or 0 for log in day["logs"])

    # 转换为 JSON 可序列化的格式
    weeks_payload = []
    for week in structured_logs:
        days_payload = []
        for day in week["days"]:
            days_payload.append(
                {
                    "date": day["date"].isoformat(),
                    "efficiency": round(day["efficiency"], 1)
                    if day["efficiency"]
                    else 0,
                    "total_duration": day["total_duration"],
                    "logs": [log.to_dict() for log in day["logs"]],
                }
            )
        weeks_payload.append(
            {
                "year": week["year"],
                "week_num": week["week_num"],
                "efficiency": round(week["efficiency"], 1) if week["efficiency"] else 0,
                "days": days_payload,
            }
        )

    return jsonify(
        {
            "success": True,
            "stage": stage.to_dict(),
            "current_sort": sort_order,
            "structured_logs": weeks_payload,
        }
    ), 200


@bp.route("", methods=["GET"])
@jwt_required()
def get_records():
    """获取学习记录列表（分页）"""
    current_user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    # 构建基础查询
    query = LogEntry.query.filter_by(user_id=current_user_id)

    # 可选的过滤条件
    category_id = request.args.get("category_id", type=int)
    if category_id:
        query = query.filter_by(category_id=category_id)

    # 按日期降序排序
    query = query.order_by(LogEntry.log_date.desc(), LogEntry.created_at.desc())

    # 分页
    paginated_records = query.paginate(page=page, per_page=per_page, error_out=False)
    records = paginated_records.items

    # 序列化
    result = [record.to_dict() for record in records]

    return jsonify(
        {
            "records": result,
            "total": paginated_records.total,
            "pages": paginated_records.pages,
            "current_page": page,
        }
    )


@bp.route("/<int:record_id>", methods=["GET"])
@jwt_required()
def get_record(record_id):
    """获取单条记录"""
    current_user_id = get_jwt_identity()

    record = (
        LogEntry.query.join(Stage)
        .filter(LogEntry.id == record_id, Stage.user_id == current_user_id)
        .first()
    )

    if not record:
        return jsonify({"success": False, "message": "记录不存在"}), 404

    return jsonify({"success": True, "record": record.to_dict()}), 200


@bp.route("", methods=["POST"])
@jwt_required()
def create_record():
    """创建学习记录（完整表单）- 与旧项目 add() 完全一致"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "请提供记录数据"}), 400

    # 验证必填字段
    if not data.get("stage_id") or not data.get("task"):
        return jsonify({"success": False, "message": "阶段和任务为必填项"}), 400

    # 验证阶段所有权
    stage = Stage.query.filter_by(id=data["stage_id"], user_id=current_user_id).first()
    if not stage:
        return jsonify({"success": False, "message": "阶段不存在"}), 404

    # 说明：当前模型通过 subcategory_id 关联分类；如果前端仍传 category_id，仅用于前端选择，不在 LogEntry 中保存。
    # 验证子分类(如果提供)
    subcategory_id = data.get("subcategory_id")
    if subcategory_id:
        subcategory = (
            SubCategory.query.join(Category)
            .filter(
                SubCategory.id == subcategory_id, Category.user_id == current_user_id
            )
            .first()
        )
        if not subcategory:
            return jsonify({"success": False, "message": "选择了无效的分类。"}), 404

    # 如果没有子分类但提供了 category_id，可给出更友好的提示（可选逻辑）
    if not subcategory_id and data.get("category_id"):
        # 前端可能只选了分类但没选标签，提醒需要选择标签
        return jsonify({"success": False, "message": "请为该分类选择一个标签（子分类）"}), 400

    try:
        # 处理时长：支持小时+分钟的格式（与旧项目一致）
        hours = int(data.get("duration_hours", 0) or 0)
        minutes = int(data.get("duration_minutes", 0) or 0)
        total_duration = (hours * 60) + minutes

        # 如果没有提供 duration_hours/minutes，尝试使用 actual_duration
        if total_duration == 0 and data.get("actual_duration"):
            total_duration = int(data.get("actual_duration"))

        record = LogEntry(
            log_date=datetime.fromisoformat(data["log_date"]).date()
            if data.get("log_date")
            else date.today(),
            time_slot=data.get("time_slot"),
            task=data["task"],
            actual_duration=total_duration,
            mood=data.get("mood", 3),  # 默认心情为 3
            notes=data.get("notes"),
            stage_id=data["stage_id"],
            subcategory_id=subcategory_id,
        )
        db.session.add(record)
        db.session.flush()  # 获取 ID
        new_log_id = record.id
        db.session.commit()

        # 更新效率数据
        record_service.update_efficiency_for_date(record.log_date, stage)

        return jsonify(
            {
                "success": True,
                "message": "新纪录添加成功!",
                "record": record.to_dict(),
                "id": new_log_id,
            }
        ), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Record creation error: {e}", exc_info=True)
        return jsonify({"success": False, "message": f"发生错误: {e}"}), 500


@bp.route("/<int:record_id>", methods=["PUT"])
@jwt_required()
def update_record(record_id):
    """更新学习记录 - 与旧项目 edit() 完全一致"""
    current_user_id = get_jwt_identity()

    record = (
        LogEntry.query.join(Stage)
        .filter(LogEntry.id == record_id, Stage.user_id == current_user_id)
        .first()
    )

    if not record:
        return jsonify(
            {"success": False, "message": "未找到要编辑的记录或无权访问。"}
        ), 404

    data = request.get_json()
    stage = record.stage
    old_date = record.log_date

    try:
        # 验证子分类(如果提供)
        subcategory_id = data.get("subcategory_id")
        if subcategory_id:
            subcategory = (
                SubCategory.query.join(Category)
                .filter(
                    SubCategory.id == subcategory_id,
                    Category.user_id == current_user_id,
                )
                .first()
            )
            if not subcategory:
                return jsonify({"success": False, "message": "选择了无效的分类。"}), 404

        # 处理时长：支持小时+分钟的格式
        if "duration_hours" in data or "duration_minutes" in data:
            hours = int(data.get("duration_hours", 0) or 0)
            minutes = int(data.get("duration_minutes", 0) or 0)
            total_duration = (hours * 60) + minutes
        elif "actual_duration" in data:
            total_duration = int(data.get("actual_duration"))
        else:
            total_duration = record.actual_duration

        # 更新字段
        if "log_date" in data:
            record.log_date = datetime.fromisoformat(data["log_date"]).date()
        if "time_slot" in data:
            record.time_slot = data["time_slot"]
        if "task" in data:
            record.task = data["task"]
        record.actual_duration = total_duration
        if "mood" in data:
            record.mood = data["mood"]
        if "notes" in data:
            record.notes = data["notes"]
        if "subcategory_id" in data:
            record.subcategory_id = subcategory_id

        db.session.commit()

        # 更新效率数据
        record_service.update_efficiency_for_date(record.log_date, stage)
        if old_date != record.log_date:
            record_service.update_efficiency_for_date(old_date, stage)

        return (
            jsonify(
                {
                    "success": True,
                    "message": "记录更新成功!",
                    "record": record.to_dict(),
                }
            ),
            200,
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Record update error: {e}", exc_info=True)
        return jsonify({"success": False, "message": f"更新时发生错误: {e}"}), 500


@bp.route("/<int:record_id>", methods=["DELETE"])
@jwt_required()
def delete_record(record_id):
    """删除学习记录 - 与旧项目 delete() 完全一致"""
    current_user_id = get_jwt_identity()

    record = (
        LogEntry.query.join(Stage)
        .filter(LogEntry.id == record_id, Stage.user_id == current_user_id)
        .first()
    )

    if not record:
        return jsonify(
            {"success": False, "message": "未找到要删除的记录或无权访问。"}
        ), 404

    date_to_update = record.log_date
    stage = record.stage

    try:
        db.session.delete(record)
        db.session.commit()

        # 更新效率数据
        record_service.update_efficiency_for_date(date_to_update, stage)

        return jsonify({"success": True, "message": "记录已删除。"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Record deletion error: {e}", exc_info=True)
        return jsonify({"success": False, "message": f"删除时发生错误: {e}"}), 500


@bp.route("/statistics", methods=["GET"])
@jwt_required()
def get_statistics():
    """
    获取统计数据
    查询参数:
    - stage_id: 阶段ID (必填)
    - start_date: 开始日期 (可选)
    - end_date: 结束日期 (可选)
    """
    current_user_id = get_jwt_identity()

    stage_id = request.args.get("stage_id", type=int)
    if not stage_id:
        return jsonify({"success": False, "message": "请指定阶段ID"}), 400

    # 验证阶段所有权
    stage = Stage.query.filter_by(id=stage_id, user_id=current_user_id).first()
    if not stage:
        return jsonify({"success": False, "message": "阶段不存在"}), 404

    # 查询条件
    filters = [LogEntry.stage_id == stage_id]

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if start_date:
        filters.append(LogEntry.log_date >= datetime.fromisoformat(start_date).date())
    if end_date:
        filters.append(LogEntry.log_date <= datetime.fromisoformat(end_date).date())

    # 统计查询
    records = LogEntry.query.filter(*filters).all()

    total_records = len(records)
    total_duration = sum(r.actual_duration or 0 for r in records)
    avg_mood = (
        sum(r.mood or 0 for r in records if r.mood)
        / len([r for r in records if r.mood])
        if records
        else 0
    )

    # 按日期分组统计
    from collections import defaultdict

    daily_stats = defaultdict(lambda: {"duration": 0, "count": 0, "avg_mood": 0})

    for record in records:
        daily_stats[record.log_date.isoformat()]["duration"] += (
            record.actual_duration or 0
        )
        daily_stats[record.log_date.isoformat()]["count"] += 1
        if record.mood:
            daily_stats[record.log_date.isoformat()]["avg_mood"] += record.mood

    return jsonify(
        {
            "success": True,
            "statistics": {
                "total_records": total_records,
                "total_duration_minutes": total_duration,
                "total_duration_hours": round(total_duration / 60, 2),
                "average_mood": round(avg_mood, 2),
                "daily": dict(daily_stats),
            },
        }
    ), 200


@bp.route("/export", methods=["GET"])
@jwt_required()
def export_data():
    """导出用户所有数据为ZIP文件"""
    current_user_id = get_jwt_identity()

    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"success": False, "message": "用户不存在"}), 404

    try:
        zip_buffer = data_service.export_data_for_user(user)
        username = user.username.replace(" ", "_")
        filename = f"{username}_backup_{date.today().isoformat()}.zip"

        return Response(
            zip_buffer,
            mimetype="application/zip",
            headers={"Content-Disposition": f"attachment;filename={filename}"},
        )
    except Exception as e:
        current_app.logger.error(f"Export error: {e}", exc_info=True)
        return jsonify({"success": False, "message": "导出失败"}), 500


@bp.route("/import", methods=["POST"])
@jwt_required()
def import_data():
    """从ZIP文件导入用户数据"""
    current_user_id = get_jwt_identity()

    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"success": False, "message": "用户不存在"}), 404

    if "file" not in request.files:
        return jsonify({"success": False, "message": "请上传文件"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "message": "文件名为空"}), 400

    if not file.filename.endswith(".zip"):
        return jsonify({"success": False, "message": "只支持ZIP文件"}), 400

    try:
        current_app.logger.info(
            f"Starting import for user {user.username} with file {file.filename}"
        )
        success, message = data_service.import_data_for_user(user, file.stream)

        if success:
            current_app.logger.info(
                f"Import successful for user {user.username}, recalculating efficiency"
            )
            # 重新计算所有阶段的效率
            all_user_stages = Stage.query.filter_by(user_id=user.id).all()
            for stage in all_user_stages:
                record_service.recalculate_efficiency_for_stage(stage)

            current_app.logger.info(
                f"Import and recalculation complete for user {user.username}"
            )
            return jsonify({"success": True, "message": message}), 200
        else:
            current_app.logger.warning(
                f"Import failed for user {user.username}: {message}"
            )
            return jsonify({"success": False, "message": message}), 400

    except Exception as e:
        current_app.logger.error(
            f"Import error for user {user.username}: {e}", exc_info=True
        )
        return jsonify({"success": False, "message": f"导入失败: {str(e)}"}), 500


@bp.route("/clear-all", methods=["POST"])
@jwt_required()
def clear_all_data():
    """清空用户所有数据"""
    current_user_id = get_jwt_identity()

    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"success": False, "message": "用户不存在"}), 404

    # 需要用户确认
    confirm = request.get_json().get("confirm", False)
    if not confirm:
        return jsonify(
            {
                "success": False,
                "message": "请在请求中设置 confirm=true 以确认清空所有数据",
            }
        ), 400

    try:
        success, message = data_service.clear_all_user_data(user)
        if success:
            return jsonify({"success": True, "message": message}), 200
        else:
            return jsonify({"success": False, "message": message}), 500
    except Exception as e:
        current_app.logger.error(f"Clear data error: {e}", exc_info=True)
        return jsonify({"success": False, "message": "清空数据失败"}), 500
