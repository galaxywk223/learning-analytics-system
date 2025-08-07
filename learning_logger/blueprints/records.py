# 文件路径: learning_logger/blueprints/records.py
import os
import sys
from datetime import date
from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, Response, jsonify, current_app, session)
from flask_login import login_required, current_user
from sqlalchemy import func

from .. import db
from ..services import record_service, data_service
from ..forms import DataImportForm
from ..models import (User, Stage, Category, SubCategory, LogEntry, DailyData,
                      WeeklyData, Motto, Todo, Milestone, MilestoneCategory,
                      MilestoneAttachment, DailyPlanItem, Setting, CountdownEvent)
from ..helpers import get_custom_week_info

records_bp = Blueprint('records', __name__)


def _get_category_data_for_form():
    all_categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    all_subcategories = {}
    for cat in all_categories:
        all_subcategories[cat.id] = [{'id': sub.id, 'name': sub.name} for sub in
                                     cat.subcategories.order_by(SubCategory.name).all()]
    return all_categories, all_subcategories


@records_bp.route('/')
@login_required
def list_records():
    all_stages = Stage.query.filter_by(user_id=current_user.id).order_by(Stage.start_date.desc()).all()
    active_stage = None
    stage_id = request.args.get('stage_id', type=int)
    if stage_id:
        active_stage = next((s for s in all_stages if s.id == stage_id), None)
        if active_stage:
            session['active_stage_id'] = active_stage.id
        else:
            flash('指定的阶段不存在。', 'error')
            return redirect(url_for('records.list_records'))
    else:
        active_stage_id = session.get('active_stage_id')
        if active_stage_id:
            active_stage = next((s for s in all_stages if s.id == active_stage_id), None)
        if not active_stage and all_stages:
            active_stage = all_stages[0]
            session['active_stage_id'] = active_stage.id
    if not active_stage:
        flash('欢迎使用！请先创建一个新的学习阶段以开始记录。', 'info')
        return redirect(url_for('stage.manage_stages'))
    sort_order = request.args.get('sort', 'desc')
    structured_logs = record_service.get_structured_logs_for_stage(active_stage, sort_order)
    for week in structured_logs:
        for day in week['days']:
            day['total_duration'] = sum(log.actual_duration for log in day['logs'] if log.actual_duration)
    return render_template('index.html', structured_logs=structured_logs, current_sort=sort_order,
                           all_stages=all_stages, active_stage=active_stage)


@records_bp.route('/form/add')
@login_required
def get_add_form():
    active_stage_id = session.get('active_stage_id')
    if not active_stage_id: return jsonify({'success': False, 'message': '请先选择一个有效的学习阶段。'})
    default_date_str = request.args.get('default_date')
    default_date_obj = date.fromisoformat(default_date_str) if default_date_str else date.today()
    all_categories, all_subcategories = _get_category_data_for_form()
    return render_template('_form_record.html', log=None, default_date=default_date_obj,
                           action_url=url_for('records.add'), submit_button_text='添加记录',
                           all_categories=all_categories, all_subcategories=all_subcategories)


@records_bp.route('/form/edit/<int:log_id>')
@login_required
def get_edit_form(log_id):
    log = record_service.get_log_entry_for_user(log_id, current_user)
    if not log: return jsonify({'success': False, 'message': '记录不存在或无权访问。'})
    all_categories, all_subcategories = _get_category_data_for_form()
    return render_template('_form_record.html', log=log, default_date=log.log_date,
                           action_url=url_for('records.edit', log_id=log.id), submit_button_text='更新记录',
                           all_categories=all_categories, all_subcategories=all_subcategories)


@records_bp.route('/add', methods=['POST'])
@login_required
def add():
    active_stage_id = session.get('active_stage_id')
    if not active_stage_id:
        return jsonify({'success': False, 'message': '无法添加记录，未找到当前活动阶段。'}), 400

    success, message, new_log_id = record_service.add_log_for_stage(active_stage_id, current_user, request.form)

    if success:
        new_log = LogEntry.query.get(new_log_id)
        html_to_insert = render_template('_log_entry_item.html', log=new_log)
        stage = Stage.query.get(active_stage_id)

        daily_data = DailyData.query.filter_by(log_date=new_log.log_date, stage_id=active_stage_id).first()
        new_daily_efficiency = round(daily_data.efficiency, 1) if daily_data else 0

        year, week_num = get_custom_week_info(new_log.log_date, stage.start_date)
        weekly_data = WeeklyData.query.filter_by(year=year, week_num=week_num, stage_id=active_stage_id).first()
        new_weekly_efficiency = round(weekly_data.efficiency, 1) if weekly_data else 0

        total_duration_minutes = db.session.query(func.sum(LogEntry.actual_duration)).filter(
            LogEntry.log_date == new_log.log_date,
            LogEntry.stage_id == active_stage_id
        ).scalar() or 0
        new_total_duration_hours = f"{total_duration_minutes / 60:.1f}h"

        return jsonify({
            'success': True,
            'message': message,
            'html': html_to_insert,
            'target_container': f"#log-table-body-{new_log.log_date.isoformat()}",
            'action': 'append',
            'updates': {
                'daily_efficiency': {
                    'target_id': f"#daily-efficiency-badge-{new_log.log_date.isoformat()}",
                    'value': f"日效率: {new_daily_efficiency}"
                },
                'weekly_efficiency': {
                    'target_id': f"#weekly-efficiency-badge-{year}-{week_num}",
                    'value': f"周平均效率: {new_weekly_efficiency}"
                },
                'daily_duration': {
                    'target_id': f"#daily-duration-text-{new_log.log_date.isoformat()}",
                    'value': new_total_duration_hours
                }
            }
        })
    else:
        current_app.logger.error(f"为阶段 {active_stage_id} 添加记录时: {message}")
        return jsonify({'success': False, 'message': message}), 400


@records_bp.route('/edit/<int:log_id>', methods=['POST'])
@login_required
def edit(log_id):
    # 你的 service 函数只返回 success 和 message，所以我们先执行更新
    success, message = record_service.update_log_for_user(log_id, current_user, request.form)

    if success:
        # 更新成功后，我们从数据库重新获取刚刚更新的对象
        updated_log = record_service.get_log_entry_for_user(log_id, current_user)
        if not updated_log:
            return jsonify({'success': False, 'message': '更新后无法重新获取记录。'}), 404

        # 渲染更新后的 HTML 片段
        html_to_replace = render_template('_log_entry_item.html', log=updated_log)

        # 重新计算相关的统计数据
        stage = updated_log.stage
        daily_data = DailyData.query.filter_by(log_date=updated_log.log_date, stage_id=updated_log.stage_id).first()
        new_daily_efficiency = round(daily_data.efficiency, 1) if daily_data else 0

        year, week_num = get_custom_week_info(updated_log.log_date, stage.start_date)
        weekly_data = WeeklyData.query.filter_by(year=year, week_num=week_num, stage_id=updated_log.stage_id).first()
        new_weekly_efficiency = round(weekly_data.efficiency, 1) if weekly_data else 0

        total_duration_minutes = db.session.query(func.sum(LogEntry.actual_duration)).filter(
            LogEntry.log_date == updated_log.log_date,
            LogEntry.stage_id == updated_log.stage_id
        ).scalar() or 0
        new_total_duration_hours = f"{total_duration_minutes / 60:.1f}h"

        return jsonify({
            'success': True,
            'message': message,
            'action': 'replace',
            'replace_target': f'#log-entry-row-{updated_log.id}',
            'html': html_to_replace,
            'updates': {
                'daily_efficiency': {
                    'target_id': f"#daily-efficiency-badge-{updated_log.log_date.isoformat()}",
                    'value': f"日效率: {new_daily_efficiency}"
                },
                'weekly_efficiency': {
                    'target_id': f"#weekly-efficiency-badge-{year}-{week_num}",
                    'value': f"周平均效率: {new_weekly_efficiency}"
                },
                'daily_duration': {
                    'target_id': f"#daily-duration-text-{updated_log.log_date.isoformat()}",
                    'value': new_total_duration_hours
                }
            }
        })
    else:
        current_app.logger.error(f"为用户 {current_user.id} 编辑记录 {log_id} 时: {message}")
        return jsonify({'success': False, 'message': message}), 400


@records_bp.route('/delete/<int:log_id>', methods=['POST'])
@login_required
def delete(log_id):
    log = record_service.get_log_entry_for_user(log_id, current_user)
    if not log:
        return jsonify({'success': False, 'message': '记录未找到或无权删除。'}), 404

    log_date = log.log_date
    stage_id = log.stage_id
    stage = log.stage
    log_row_id = f"#log-entry-row-{log.id}"

    success, message = record_service.delete_log_for_user(log_id, current_user)

    if success:
        remaining_logs_count = LogEntry.query.filter_by(log_date=log_date, stage_id=stage_id).count()

        if remaining_logs_count > 0:
            daily_data = DailyData.query.filter_by(log_date=log_date, stage_id=stage_id).first()
            new_daily_efficiency = round(daily_data.efficiency, 1) if daily_data else 0

            year, week_num = get_custom_week_info(log_date, stage.start_date)
            weekly_data = WeeklyData.query.filter_by(year=year, week_num=week_num, stage_id=stage_id).first()
            new_weekly_efficiency = round(weekly_data.efficiency, 1) if weekly_data else 0

            total_duration_minutes = db.session.query(func.sum(LogEntry.actual_duration)).filter(
                LogEntry.log_date == log_date,
                LogEntry.stage_id == stage_id
            ).scalar() or 0
            new_total_duration_hours = f"{total_duration_minutes / 60:.1f}h"

            return jsonify({
                'success': True,
                'message': message,
                'remove_target': log_row_id,
                'updates': {
                    'daily_efficiency': {
                        'target_id': f"#daily-efficiency-badge-{log_date.isoformat()}",
                        'value': f"日效率: {new_daily_efficiency}"
                    },
                    'weekly_efficiency': {
                        'target_id': f"#weekly-efficiency-badge-{year}-{week_num}",
                        'value': f"周平均效率: {new_weekly_efficiency}"
                    },
                    'daily_duration': {
                        'target_id': f"#daily-duration-text-{log_date.isoformat()}",
                        'value': new_total_duration_hours
                    }
                }
            })
        else:
            return jsonify({'success': True, 'message': message, 'reload': True})
    else:
        current_app.logger.error(f"为用户 {current_user.id} 删除记录 {log_id} 时: {message}")
        return jsonify({'success': False, 'message': message}), 400


@records_bp.route('/settings/data')
@login_required
def settings_data():
    form = DataImportForm()
    return render_template('settings_data.html', form=form)


@records_bp.route('/export/zip')
@login_required
def export_zip():
    zip_buffer = data_service.export_data_for_user(current_user)
    username = current_user.username.replace(" ", "_")
    filename = f"{username}_backup_{date.today().isoformat()}.zip"
    return Response(zip_buffer, mimetype="application/zip",
                    headers={"Content-Disposition": f"attachment;filename={filename}"})


@records_bp.route('/import/zip', methods=['POST'])
@login_required
def import_zip():
    form = DataImportForm()
    if form.validate_on_submit():
        file_storage = form.file.data
        success, message = data_service.import_data_for_user(current_user, file_storage.stream)
        if success:
            current_app.logger.info("Import successful. Triggering full efficiency recalculation for all stages.")
            all_user_stages = Stage.query.filter_by(user_id=current_user.id).all()
            for stage in all_user_stages:
                record_service.recalculate_efficiency_for_stage(stage)
            current_app.logger.info("Full efficiency recalculation finished.")
            flash(message, 'success')
            return redirect(url_for('records.list_records'))
        else:
            current_app.logger.error(f"Import failed for user {current_user.id}: {message}")
            flash(message, 'error')
            return redirect(url_for('records.settings_data'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'danger')
        return redirect(url_for('records.settings_data'))


@records_bp.route('/clear_data', methods=['POST'])
@login_required
def clear_data():
    user_id = current_user.id
    try:
        upload_folder = current_app.config.get('MILESTONE_UPLOADS')
        if upload_folder:
            milestones = Milestone.query.filter_by(user_id=user_id).all()
            for m in milestones:
                for att in m.attachments:
                    try:
                        full_path = os.path.join(upload_folder, att.file_path)
                        if os.path.exists(full_path):
                            os.remove(full_path)
                    except Exception as e:
                        current_app.logger.error(f"附件文件删除失败 {att.file_path}: {e}")

        stage_ids = [s.id for s in Stage.query.filter_by(user_id=user_id).with_entities(Stage.id)]
        category_ids = [c.id for c in Category.query.filter_by(user_id=user_id).with_entities(Category.id)]
        milestone_ids = [m.id for m in Milestone.query.filter_by(user_id=user_id).with_entities(Milestone.id)]

        if milestone_ids: MilestoneAttachment.query.filter(
            MilestoneAttachment.milestone_id.in_(milestone_ids)).delete(
            synchronize_session=False)
        if stage_ids:
            LogEntry.query.filter(LogEntry.stage_id.in_(stage_ids)).delete(synchronize_session=False)
            DailyData.query.filter(DailyData.stage_id.in_(stage_ids)).delete(synchronize_session=False)
            WeeklyData.query.filter(WeeklyData.stage_id.in_(stage_ids)).delete(synchronize_session=False)
        if category_ids: SubCategory.query.filter(SubCategory.category_id.in_(category_ids)).delete(
            synchronize_session=False)

        Motto.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        Todo.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        CountdownEvent.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        DailyPlanItem.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        Setting.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        if milestone_ids: Milestone.query.filter(Milestone.id.in_(milestone_ids)).delete(synchronize_session=False)
        MilestoneCategory.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        if category_ids: Category.query.filter(Category.id.in_(category_ids)).delete(synchronize_session=False)
        if stage_ids: Stage.query.filter(Stage.id.in_(stage_ids)).delete(synchronize_session=False)

        db.session.commit()
        flash('您的所有个人数据（包括附件）已被成功清空！', 'success')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"清空用户 {user_id} 数据时发生严重错误: {e}", exc_info=True)
        flash(f"清空数据时发生严重错误: {e}", 'error')
    return redirect(url_for('records.settings_data'))
