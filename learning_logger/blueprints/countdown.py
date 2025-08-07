# 文件路径: learning_logger/blueprints/countdown.py
from datetime import date, datetime
import pytz

from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, jsonify, current_app, session)
from flask_login import login_required, current_user

from .. import db
from ..models import CountdownEvent, Stage
from ..helpers import get_custom_week_info

countdown_bp = Blueprint('countdown', __name__, url_prefix='/countdown')

BEIJING_TZ = pytz.timezone('Asia/Shanghai')


@countdown_bp.route('/')
@login_required
def list_events():
    """
    显示当前用户的所有倒计时事件的列表。
    """
    now_utc = datetime.now(pytz.utc)

    all_events = CountdownEvent.query.filter_by(
        user_id=current_user.id
    ).order_by(CountdownEvent.target_datetime_utc.asc()).all()

    active_events = []
    expired_events = []

    active_stage_id = session.get('active_stage_id')
    active_stage = Stage.query.get(active_stage_id) if active_stage_id else None

    current_relative_time = "请先选择或创建一个学习阶段"
    if active_stage:
        start_date = active_stage.start_date
        now_beijing = now_utc.astimezone(BEIJING_TZ)
        _, week_num = get_custom_week_info(now_beijing.date(), start_date)
        day_map = {0: '一', 1: '二', 2: '三', 3: '四', 4: '五', 5: '六', 6: '日'}
        day_of_week_str = day_map.get(now_beijing.weekday(), '')
        hour = now_beijing.hour
        time_of_day_str = "凌晨" if 0 <= hour < 6 else "上午" if hour < 12 else "中午" if hour < 14 else "下午" if hour < 18 else "晚上"
        current_relative_time = f"{active_stage.name} - 第 {week_num} 周周{day_of_week_str}{time_of_day_str}"

    for event in all_events:
        if event.target_datetime_utc.tzinfo is None:
            event.target_datetime_utc = pytz.utc.localize(event.target_datetime_utc)

        event.target_datetime_beijing = event.target_datetime_utc.astimezone(BEIJING_TZ)
        event.target_iso_utc = event.target_datetime_utc.isoformat()

        if event.target_datetime_utc < now_utc:
            event.is_expired = True
            expired_events.append(event)
        else:
            event.is_expired = False

            if event.created_at_utc:

                if event.created_at_utc.tzinfo is None:
                    event.created_at_utc = pytz.utc.localize(event.created_at_utc)

                time_remaining = event.target_datetime_utc - now_utc
                total_delta = event.target_datetime_utc - event.created_at_utc
                elapsed_delta = now_utc - event.created_at_utc

                if total_delta.total_seconds() > 0:
                    event.progress_percentage = min((elapsed_delta.total_seconds() / total_delta.total_seconds()) * 100,
                                                    100)
                else:
                    event.progress_percentage = 100

                if time_remaining.days < 1:
                    event.card_status = 'urgent'
                elif time_remaining.days < 7:
                    event.card_status = 'warning'
                else:
                    event.card_status = 'normal'
            else:

                event.progress_percentage = 0
                event.card_status = 'normal'

            active_events.append(event)

    expired_events.sort(key=lambda x: x.target_datetime_utc, reverse=True)

    return render_template(
        'countdown.html',
        active_events=active_events,
        expired_events=expired_events,
        current_relative_time=current_relative_time
    )


@countdown_bp.route('/form/add')
@login_required
def get_add_form():
    return render_template('_form_countdown.html', event=None, action_url=url_for('countdown.add'),
                           submit_button_text='添加目标')


@countdown_bp.route('/form/edit/<int:event_id>')
@login_required
def get_edit_form(event_id):
    event = CountdownEvent.query.filter_by(id=event_id, user_id=current_user.id).first_or_404()
    event.target_datetime_beijing = event.target_datetime_utc.astimezone(BEIJING_TZ)
    return render_template('_form_countdown.html', event=event, action_url=url_for('countdown.edit', event_id=event.id),
                           submit_button_text='更新目标')


def _process_form_and_get_utc_datetime():
    title = request.form.get('title')
    target_date_str = request.form.get('target_date')
    target_time_str = request.form.get('target_time') or "00:00"
    if not all([title, target_date_str]):
        raise ValueError("目标名称和日期是必填项。")
    local_dt_naive = datetime.strptime(f"{target_date_str} {target_time_str}", '%Y-%m-%d %H:%M')
    local_dt_aware = BEIJING_TZ.localize(local_dt_naive)
    return title, local_dt_aware.astimezone(pytz.utc)


# 在 learning_logger/blueprints/countdown.py 中
@countdown_bp.route('/add', methods=['POST'])
@login_required
def add():
    try:
        title, utc_dt = _process_form_and_get_utc_datetime()
        new_event = CountdownEvent(title=title, target_datetime_utc=utc_dt, user_id=current_user.id)
        db.session.add(new_event)
        db.session.commit()  # 先提交以获取 new_event.id 和其他默认值

        # --- 新增逻辑：准备渲染新卡片所需的数据 ---
        now_utc = datetime.now(pytz.utc)
        # 确保时区信息正确
        if new_event.target_datetime_utc.tzinfo is None:
            new_event.target_datetime_utc = pytz.utc.localize(new_event.target_datetime_utc)
        if new_event.created_at_utc.tzinfo is None:
            new_event.created_at_utc = pytz.utc.localize(new_event.created_at_utc)

        new_event.target_datetime_beijing = new_event.target_datetime_utc.astimezone(BEIJING_TZ)
        new_event.target_iso_utc = new_event.target_datetime_utc.isoformat()

        # 计算进度和状态
        time_remaining = new_event.target_datetime_utc - now_utc
        total_delta = new_event.target_datetime_utc - new_event.created_at_utc
        elapsed_delta = now_utc - new_event.created_at_utc

        if total_delta.total_seconds() > 0:
            new_event.progress_percentage = min((elapsed_delta.total_seconds() / total_delta.total_seconds()) * 100,
                                                100)
        else:
            new_event.progress_percentage = 100

        if time_remaining.days < 1:
            new_event.card_status = 'urgent'
        elif time_remaining.days < 7:
            new_event.card_status = 'warning'
        else:
            new_event.card_status = 'normal'
        # --- 新增逻辑结束 ---

        # 渲染新卡片的 HTML
        html_to_add = render_template('_countdown_item.html', event=new_event)

        # 返回包含 HTML 和目标容器的完整 JSON
        return jsonify({
            'success': True,
            'message': f'新的倒计时目标 “{title}” 已添加！',
            'html': html_to_add,
            'target_container': '#active-events-container',
            'action': 'prepend'  # 'prepend' 会让新项显示在最前面
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"添加倒计时事件时出错: {e}")
        return jsonify({'success': False, 'message': f'添加目标时出错: {str(e)}'}), 400


# 在 learning_logger/blueprints/countdown.py 中
@countdown_bp.route('/edit/<int:event_id>', methods=['POST'])
@login_required
def edit(event_id):
    event = CountdownEvent.query.filter_by(id=event_id, user_id=current_user.id).first_or_404()
    try:
        title, utc_dt = _process_form_and_get_utc_datetime()
        event.title = title
        event.target_datetime_utc = utc_dt
        db.session.commit() # 提交更新

        # --- 复用之前的逻辑，准备渲染卡片所需的数据 ---
        now_utc = datetime.now(pytz.utc)
        if event.target_datetime_utc.tzinfo is None:
            event.target_datetime_utc = pytz.utc.localize(event.target_datetime_utc)
        if event.created_at_utc.tzinfo is None:
            event.created_at_utc = pytz.utc.localize(event.created_at_utc)

        event.target_datetime_beijing = event.target_datetime_utc.astimezone(BEIJING_TZ)
        event.target_iso_utc = event.target_datetime_utc.isoformat()

        time_remaining = event.target_datetime_utc - now_utc
        total_delta = event.target_datetime_utc - event.created_at_utc
        elapsed_delta = now_utc - event.created_at_utc

        if total_delta.total_seconds() > 0:
            event.progress_percentage = min((elapsed_delta.total_seconds() / total_delta.total_seconds()) * 100, 100)
        else:
            event.progress_percentage = 100

        if time_remaining.days < 1:
            event.card_status = 'urgent'
        elif time_remaining.days < 7:
            event.card_status = 'warning'
        else:
            event.card_status = 'normal'
        # --- 数据准备结束 ---

        # 渲染更新后的卡片 HTML
        html_to_replace = render_template('_countdown_item.html', event=event)

        # 返回包含替换指令、目标和新HTML的JSON
        return jsonify({
            'success': True,
            'message': f'目标 “{title}” 已更新！',
            'action': 'replace',
            'replace_target': f'#countdown-{event.id}', # 指定要替换哪个元素
            'html': html_to_replace
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"编辑事件 {event_id} 时出错: {e}")
        return jsonify({'success': False, 'message': f'更新目标时出错: {str(e)}'}), 400

@countdown_bp.route('/delete/<int:event_id>', methods=['POST'])
@login_required
def delete(event_id):
    event = CountdownEvent.query.filter_by(id=event_id, user_id=current_user.id).first_or_404()
    try:
        title = event.title
        db.session.delete(event)
        db.session.commit()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': f'目标 “{title}” 已删除。'})
        flash(f'目标 “{title}” 已删除。', 'info')
        return redirect(url_for('countdown.list_events'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除事件 {event_id} 时出错: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': f'删除目标时出错: {e}'}), 400
        flash(f'删除目标时出错: {e}', 'error')
        return redirect(url_for('countdown.list_events'))
