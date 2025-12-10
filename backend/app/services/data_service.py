# -*- coding: utf-8 -*-
"""数据导入导出服务"""

import io
import json
import os
import zipfile
from datetime import date, datetime

from flask import current_app

from app import db
from app.models import (
    Category,
    CountdownEvent,
    DailyData,
    LogEntry,
    Milestone,
    MilestoneAttachment,
    MilestoneCategory,
    Motto,
    Setting,
    Stage,
    SubCategory,
    WeeklyData,
)

MODELS_TO_HANDLE = [
    Setting,
    Stage,
    Category,
    SubCategory,
    LogEntry,
    DailyData,
    WeeklyData,
    Motto,
    MilestoneCategory,
    Milestone,
    MilestoneAttachment,
    CountdownEvent,
]

# 缓存各模型的真实字段，用于导入时剔除派生属性
MODEL_COLUMN_MAP = {
    model.__tablename__: {column.name for column in model.__table__.columns}
    for model in MODELS_TO_HANDLE
}

# 对于用户私有且没有被其它表引用其主键的叶子表,导入时忽略提供的 id, 交由数据库自增
# 这样可避免不同用户/历史备份之间的主键碰撞
LEAF_USER_TABLES = (
    Motto,
    CountdownEvent,
)


def _prune_unknown_fields(table_name: str, payload: dict) -> dict:
    """Drop keys that are not actual table columns to avoid assigning read-only properties."""
    allowed = MODEL_COLUMN_MAP.get(table_name)
    if not allowed:
        return payload
    return {key: value for key, value in payload.items() if key in allowed}


def _query_user_records(model, user_id):
    """Return all rows for the given model that belong to user_id."""
    if "user_id" in model.__table__.columns:
        return model.query.filter(model.user_id == user_id).all()

    if hasattr(model, "stage") and "stage_id" in model.__table__.columns:
        return model.query.join(Stage).filter(Stage.user_id == user_id).all()

    if hasattr(model, "milestone") and "milestone_id" in model.__table__.columns:
        return model.query.join(Milestone).filter(Milestone.user_id == user_id).all()

    if hasattr(model, "category") and "category_id" in model.__table__.columns:
        return model.query.join(Category).filter(Category.user_id == user_id).all()

    return []


def _clear_user_data(user):
    """
    在导入前,安全地清空用户的所有关联数据。
    这是一个关键步骤,以避免主键或外键冲突。
    """
    current_app.logger.info(
        f"Starting to clear all data for user: {user.username} (ID: {user.id})"
    )

    upload_folder = current_app.config.get("UPLOAD_FOLDER")
    if upload_folder:
        user_upload_folder = os.path.join(upload_folder, str(user.id))
        if os.path.exists(user_upload_folder):
            for filename in os.listdir(user_upload_folder):
                try:
                    os.remove(os.path.join(user_upload_folder, filename))
                except Exception as e:  # pragma: no cover - defensive logging
                    current_app.logger.error(
                        f"Failed to remove attachment file {filename}: {e}"
                    )
        current_app.logger.info("Cleared physical milestone attachments.")
    else:
        current_app.logger.warning(
            "UPLOAD_FOLDER not configured, skipping attachments cleanup."
        )

    MilestoneAttachment.query.filter(
        MilestoneAttachment.milestone.has(user_id=user.id)
    ).delete(synchronize_session=False)
    LogEntry.query.filter(LogEntry.stage.has(user_id=user.id)).delete(
        synchronize_session=False
    )
    SubCategory.query.filter(SubCategory.category.has(user_id=user.id)).delete(
        synchronize_session=False
    )

    DailyData.query.filter(DailyData.stage.has(user_id=user.id)).delete(
        synchronize_session=False
    )
    WeeklyData.query.filter(WeeklyData.stage.has(user_id=user.id)).delete(
        synchronize_session=False
    )
    Milestone.query.filter_by(user_id=user.id).delete(synchronize_session=False)

    Motto.query.filter_by(user_id=user.id).delete(synchronize_session=False)

    CountdownEvent.query.filter_by(user_id=user.id).delete(synchronize_session=False)

    Setting.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    Category.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    MilestoneCategory.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    Stage.query.filter_by(user_id=user.id).delete(synchronize_session=False)

    db.session.commit()
    current_app.logger.info(
        f"Successfully cleared all database entries for user: {user.username}"
    )


def export_data_for_user(user):
    """
    将指定用户的所有数据导出到一个ZIP压缩包的内存缓冲区中。
    返回: (success_bool, buffer, filename)
    """
    current_app.logger.info(f"Starting data export for user: {user.username}")
    buffer = io.BytesIO()

    try:
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for model in MODELS_TO_HANDLE:
                records = _query_user_records(model, user.id)
                data = [record.to_dict() for record in records]
                json_data = json.dumps(data, indent=4, ensure_ascii=False)
                zf.writestr(f"data/{model.__tablename__}.json", json_data)

            current_app.logger.info("Exported all database tables to JSON.")

            upload_folder = current_app.config.get("UPLOAD_FOLDER")
            current_app.logger.info(f"[导出附件] UPLOAD_FOLDER配置: {upload_folder}")

            if upload_folder:
                user_upload_folder = os.path.join(upload_folder, str(user.id))
                current_app.logger.info(
                    f"[导出附件] 用户附件目录: {user_upload_folder}"
                )
                current_app.logger.info(
                    f"[导出附件] 目录是否存在: {os.path.exists(user_upload_folder)}"
                )

                if os.path.exists(user_upload_folder):
                    files = os.listdir(user_upload_folder)
                    current_app.logger.info(f"[导出附件] 找到 {len(files)} 个文件")

                    for filename in files:
                        file_path = os.path.join(user_upload_folder, filename)
                        current_app.logger.info(f"[导出附件] 正在添加文件: {filename}")
                        zf.write(file_path, arcname=f"attachments/{filename}")
                    current_app.logger.info("Exported all milestone attachments.")
                else:
                    current_app.logger.warning(
                        f"[导出附件] 用户附件目录不存在: {user_upload_folder}"
                    )
            else:
                current_app.logger.warning(
                    "UPLOAD_FOLDER not configured, skipping attachments export."
                )

        buffer.seek(0)
        filename = f"yinghuoji_backup_{user.username}.zip"
        return True, buffer, filename
    except Exception as e:
        current_app.logger.error(
            f"Data export failed for user {user.username}: {e}", exc_info=True
        )
        return False, None, None


def import_data_for_user(user, zip_stream):
    """
    从 zip 流导入数据到指定用户，导入前会清空用户已有数据。
    """
    if not zip_stream:
        return False, "未提供 zip 文件"

    try:
        with zipfile.ZipFile(zip_stream) as zf:
            _clear_user_data(user)

            model_map = {model.__tablename__: model for model in MODELS_TO_HANDLE}
            import_order = [
                Setting.__tablename__,
                Stage.__tablename__,
                Category.__tablename__,
                SubCategory.__tablename__,
                MilestoneCategory.__tablename__,
                Milestone.__tablename__,
                LogEntry.__tablename__,
                DailyData.__tablename__,
                WeeklyData.__tablename__,
                MilestoneAttachment.__tablename__,
                CountdownEvent.__tablename__,
                Motto.__tablename__,
                CountdownEvent.__tablename__,
                Motto.__tablename__,
            ]

            pending_records = {}
            for table_name in import_order:
                json_path = f"data/{table_name}.json"
                if json_path in zf.namelist():
                    with zf.open(json_path) as json_file:
                        pending_records[table_name] = json.load(json_file)

            id_maps = {
                Stage.__tablename__: {},
                Category.__tablename__: {},
                SubCategory.__tablename__: {},
                MilestoneCategory.__tablename__: {},
                Milestone.__tablename__: {},
            }

            category_name_cache: dict[str, int] = {}
            subcategory_name_cache: dict[str, int] = {}

            def _store_mapping(bucket: str, original_id, new_id):
                if original_id is None:
                    return
                id_maps[bucket][str(original_id)] = new_id

            def _map_id(bucket: str, incoming_id):
                if incoming_id is None:
                    return None
                return id_maps[bucket].get(str(incoming_id))

            def _ensure_category_from_info(cat_info):
                if not cat_info:
                    return None

                original_id = cat_info.get("id")
                if original_id:
                    mapped = _map_id(Category.__tablename__, original_id)
                    if mapped:
                        return mapped

                name = cat_info.get("name")
                if not name:
                    return None

                if name in category_name_cache:
                    cat_id = category_name_cache[name]
                    if original_id:
                        _store_mapping(Category.__tablename__, original_id, cat_id)
                    return cat_id

                existing = Category.query.filter_by(name=name, user_id=user.id).first()
                if existing:
                    category_name_cache[name] = existing.id
                    if original_id:
                        _store_mapping(Category.__tablename__, original_id, existing.id)
                    return existing.id

                new_category = Category(name=name, user_id=user.id)
                db.session.add(new_category)
                db.session.flush()
                category_name_cache[name] = new_category.id
                if original_id:
                    _store_mapping(Category.__tablename__, original_id, new_category.id)
                current_app.logger.info(
                    "Reconstructed missing category '%s' (new id=%s)",
                    name,
                    new_category.id,
                )
                return new_category.id

            def _ensure_subcategory_from_info(sub_info, fallback_original_id=None):
                if not sub_info and not fallback_original_id:
                    return None

                original_id = sub_info.get("id") if sub_info else fallback_original_id
                if original_id:
                    mapped = _map_id(SubCategory.__tablename__, original_id)
                    if mapped:
                        return mapped

                name = (sub_info or {}).get("name")
                category_id_hint = (sub_info or {}).get("category_id")
                category_info = (sub_info or {}).get("category")

                mapped_category = _map_id(Category.__tablename__, category_id_hint)
                if mapped_category is None:
                    mapped_category = _ensure_category_from_info(category_info)
                if mapped_category is None and category_id_hint is not None:
                    mapped_category = _map_id(
                        MilestoneCategory.__tablename__, category_id_hint
                    )

                if mapped_category is None:
                    current_app.logger.warning(
                        "Unable to recreate subcategory '%s' because category mapping is missing.",
                        name or original_id,
                    )
                    return None

                cache_key = f"{mapped_category}:{name}"
                if cache_key in subcategory_name_cache:
                    sub_id = subcategory_name_cache[cache_key]
                    if original_id:
                        _store_mapping(SubCategory.__tablename__, original_id, sub_id)
                    return sub_id

                new_name = name or f"未命名标签-{original_id or mapped_category}"
                new_sub = SubCategory(name=new_name, category_id=mapped_category)
                db.session.add(new_sub)
                db.session.flush()
                subcategory_name_cache[cache_key] = new_sub.id
                if original_id:
                    _store_mapping(SubCategory.__tablename__, original_id, new_sub.id)
                current_app.logger.info(
                    "Reconstructed missing subcategory '%s' (new id=%s, category_id=%s)",
                    new_name,
                    new_sub.id,
                    mapped_category,
                )
                return new_sub.id

            for table_name in import_order:
                model = model_map.get(table_name)
                if not model:
                    continue

                records = pending_records.get(table_name, [])
                if not records:
                    continue

                for record in records:
                    record_data = dict(record)
                    original_id = record_data.pop("id", None)
                    sub_info = (
                        record_data.get("subcategory")
                        if table_name == LogEntry.__tablename__
                        else None
                    )
                    if table_name == LogEntry.__tablename__:
                        record_data.pop("subcategory", None)

                    if "user_id" in model.__table__.columns:
                        record_data["user_id"] = user.id

                    for key, value in list(record_data.items()):
                        if isinstance(value, str) and value:
                            if (
                                "datetime" in key
                                or key.endswith("_at")
                                or key.endswith("_utc")
                            ):
                                try:
                                    dt_obj = datetime.fromisoformat(
                                        value.replace("Z", "+00:00")
                                    )
                                    record_data[key] = dt_obj.replace(tzinfo=None)
                                except ValueError as ve:
                                    current_app.logger.warning(
                                        f"Could not parse datetime string '{value}' for key '{key}': {ve}"
                                    )
                            elif "date" in key and not key.endswith("_at"):
                                try:
                                    record_data[key] = date.fromisoformat(value)
                                except ValueError as ve:
                                    current_app.logger.warning(
                                        f"Could not parse date string '{value}' for key '{key}': {ve}"
                                    )

                    record_data = _prune_unknown_fields(table_name, record_data)

                    try:
                        if table_name == Stage.__tablename__:
                            new_stage = model(**record_data)
                            db.session.add(new_stage)
                            db.session.flush()
                            _store_mapping(table_name, original_id, new_stage.id)
                            continue

                        if table_name == Category.__tablename__:
                            new_category = model(**record_data)
                            db.session.add(new_category)
                            db.session.flush()
                            _store_mapping(table_name, original_id, new_category.id)
                            category_name_cache[new_category.name] = new_category.id
                            continue

                        if table_name == MilestoneCategory.__tablename__:
                            new_mc = model(**record_data)
                            db.session.add(new_mc)
                            db.session.flush()
                            _store_mapping(table_name, original_id, new_mc.id)
                            continue

                        if table_name == SubCategory.__tablename__:
                            parent_id = _map_id(
                                Category.__tablename__, record_data.get("category_id")
                            )
                            if parent_id is None:
                                current_app.logger.warning(
                                    "Skipping sub_category %s due to missing category mapping",
                                    record_data.get("name"),
                                )
                                continue
                            record_data["category_id"] = parent_id
                            new_sub = model(**record_data)
                            db.session.add(new_sub)
                            db.session.flush()
                            _store_mapping(table_name, original_id, new_sub.id)
                            sub_key = f"{parent_id}:{new_sub.name}"
                            subcategory_name_cache[sub_key] = new_sub.id
                            continue

                        if table_name == Milestone.__tablename__:
                            category_id = record_data.get("category_id")
                            if category_id is not None:
                                record_data["category_id"] = _map_id(
                                    MilestoneCategory.__tablename__, category_id
                                )
                            new_milestone = model(**record_data)
                            db.session.add(new_milestone)
                            db.session.flush()
                            _store_mapping(table_name, original_id, new_milestone.id)
                            continue

                        if table_name == LogEntry.__tablename__:
                            mapped_stage = _map_id(
                                Stage.__tablename__, record_data.get("stage_id")
                            )
                            if mapped_stage is None:
                                current_app.logger.warning(
                                    "Skipping log entry dated %s due to missing stage mapping",
                                    record_data.get("log_date"),
                                )
                                continue
                            record_data["stage_id"] = mapped_stage
                            sub_old = record_data.get("subcategory_id")
                            mapped_sub = _map_id(SubCategory.__tablename__, sub_old)
                            if not mapped_sub:
                                mapped_sub = _ensure_subcategory_from_info(
                                    sub_info, sub_old
                                )
                            record_data["subcategory_id"] = mapped_sub
                            db.session.add(model(**record_data))
                            continue

                        if table_name in {
                            DailyData.__tablename__,
                            WeeklyData.__tablename__,
                        }:
                            mapped_stage = _map_id(
                                Stage.__tablename__, record_data.get("stage_id")
                            )
                            if mapped_stage is None:
                                current_app.logger.warning(
                                    "Skipping %s record due to missing stage mapping",
                                    table_name,
                                )
                                continue
                            record_data["stage_id"] = mapped_stage
                            db.session.add(model(**record_data))
                            continue

                        if table_name == MilestoneAttachment.__tablename__:
                            milestone_id = _map_id(
                                Milestone.__tablename__, record_data.get("milestone_id")
                            )
                            if milestone_id is None:
                                current_app.logger.warning(
                                    "Skipping milestone attachment because parent milestone was not imported."
                                )
                                continue
                            record_data["milestone_id"] = milestone_id
                            original_path = record_data.get("file_path")
                            if original_path:
                                filename = os.path.basename(original_path)
                                record_data["file_path"] = f"{user.id}/{filename}"
                            db.session.add(model(**record_data))
                            continue

                        db.session.add(model(**record_data))
                    except Exception as e:  # pragma: no cover - defensive logging
                        current_app.logger.error(
                            f"Failed to add {model.__name__} record: {e}, data: {record_data}"
                        )
                        raise

            current_app.logger.info("Imported all JSON data to database session.")

            upload_folder = current_app.config.get("UPLOAD_FOLDER")
            if upload_folder:
                user_upload_folder = os.path.join(upload_folder, str(user.id))
                os.makedirs(user_upload_folder, exist_ok=True)
                for file_info in zf.infolist():
                    if file_info.filename.startswith("attachments/"):
                        zf.extract(file_info, path=user_upload_folder)

                        source_path = os.path.join(user_upload_folder, file_info.filename)
                        target_name = os.path.basename(file_info.filename)
                        base, ext = os.path.splitext(target_name)
                        dest_path = os.path.join(user_upload_folder, target_name)
                        counter = 1
                        while os.path.exists(dest_path):
                            dest_path = os.path.join(
                                user_upload_folder, f"{base}_{counter}{ext}"
                            )
                            counter += 1
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        os.rename(source_path, dest_path)

                attachments_dir = os.path.join(user_upload_folder, "attachments")
                if os.path.isdir(attachments_dir):
                    for root, dirs, files in os.walk(attachments_dir, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    try:
                        os.rmdir(attachments_dir)
                    except OSError:
                        pass
                current_app.logger.info("Extracted all attachments.")
            else:
                current_app.logger.warning(
                    "UPLOAD_FOLDER not configured, skipping attachments import."
                )

        db.session.commit()
        current_app.logger.info("Data import committed successfully.")
        return True, "导入成功"

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Data import failed for user {user.username}: {e}", exc_info=True
        )
        return False, f"导入失败: {e}"


def clear_all_user_data(user):
    """
    清空用户的所有数据(包括附件)
    """
    try:
        _clear_user_data(user)
        return True, "您的所有个人数据(包括附件)已被成功清空!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"清空用户 {user.id} 数据时发生严重错误: {e}", exc_info=True
        )
        return False, f"清空数据时发生严重错误: {e}"
