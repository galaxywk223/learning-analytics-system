"""
AI planning and analysis service using Google Gemini.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from flask import current_app
from google.api_core.exceptions import GoogleAPIError

try:
    from google import genai as genai_sdk
except ImportError:  # pragma: no cover - handled at runtime
    genai_sdk = None  # type: ignore[assignment]

from app import db
from app.models import AIInsight, DailyData, LogEntry, Stage, SubCategory


SCOPE_LABELS = {
    "day": "日度",
    "week": "周度",
    "month": "月度",
    "stage": "阶段",
}

# Cache a single client per API key to avoid re-instantiating the SDK on every call.
_gemini_client_cache: Dict[str, Any] = {}


class AIPlannerError(Exception):
    """Custom error for AI planner issues."""


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise AIPlannerError("日期格式应为 YYYY-MM-DD") from exc


def _get_date_range_for_scope(
    scope: str,
    date_str: Optional[str],
    stage_id: Optional[int],
    user_id: int,
) -> Tuple[Optional[date], Optional[date], Optional[Stage]]:
    """
    Resolve the analysis window based on scope and parameters.
    """
    scope = scope.lower()
    if scope not in SCOPE_LABELS:
        raise AIPlannerError("暂不支持的分析范围")

    if scope == "stage":
        if not stage_id:
            raise AIPlannerError("请选择要分析的阶段")
        stage = Stage.query.filter_by(id=stage_id, user_id=user_id).first()
        if not stage:
            raise AIPlannerError("阶段不存在或无权访问")
        start = stage.start_date
        # determine end date as last log for stage or today whichever later
        last_log = (
            LogEntry.query.filter_by(stage_id=stage.id)
            .order_by(LogEntry.log_date.desc())
            .first()
        )
        end = last_log.log_date if last_log else date.today()
        return start, end, stage

    if not date_str:
        target_date = date.today()
    else:
        target_date = _parse_date(date_str)

    if scope == "day":
        return target_date, target_date, None
    if scope == "week":
        # 将传入日期视为该周任意一天，周一为开始
        weekday = target_date.weekday()  # Monday=0
        start = target_date - timedelta(days=weekday)
        end = start + timedelta(days=6)
        return start, end, None
    if scope == "month":
        start = target_date.replace(day=1)
        # next month
        if start.month == 12:
            next_month = start.replace(year=start.year + 1, month=1, day=1)
        else:
            next_month = start.replace(month=start.month + 1, day=1)
        end = next_month - timedelta(days=1)
        return start, end, None

    raise AIPlannerError("不支持的分析范围")


def _get_next_range(
    scope: str,
    start: Optional[date],
    end: Optional[date],
    stage: Optional[Stage],
    user_id: int,
) -> Tuple[Optional[date], Optional[date], Optional[str]]:
    """
    Determine the next planning window based on scope.
    Returns start, end, and optional label (e.g. 下一阶段名称)
    """
    scope = scope.lower()
    if scope == "day":
        if not end:
            return None, None, None
        next_day = end + timedelta(days=1)
        return next_day, next_day, None
    if scope == "week":
        if not end:
            return None, None, None
        next_start = end + timedelta(days=1)
        next_end = next_start + timedelta(days=6)
        return next_start, next_end, None
    if scope == "month":
        if not start:
            return None, None, None
        if start.month == 12:
            next_start = start.replace(year=start.year + 1, month=1, day=1)
        else:
            next_start = start.replace(month=start.month + 1, day=1)
        if next_start.month == 12:
            next_next = next_start.replace(year=next_start.year + 1, month=1, day=1)
        else:
            next_next = next_start.replace(month=next_start.month + 1, day=1)
        next_end = next_next - timedelta(days=1)
        return next_start, next_end, None
    if scope == "stage":
        if not stage:
            return None, None, None
        next_stage = (
            Stage.query.filter(
                Stage.user_id == user_id, Stage.start_date > stage.start_date
            )
            .order_by(Stage.start_date.asc())
            .first()
        )
        if next_stage:
            next_last_log = (
                LogEntry.query.filter_by(stage_id=next_stage.id)
                .order_by(LogEntry.log_date.desc())
                .first()
            )
            if next_last_log and next_last_log.log_date:
                next_end = next_last_log.log_date
            else:
                next_end = max(date.today(), next_stage.start_date)
            return next_stage.start_date, next_end, next_stage.name
        # fallback: plan for two weeks after current stage ends
        if end:
            fallback_start = end + timedelta(days=1)
            fallback_end = fallback_start + timedelta(days=13)
            return fallback_start, fallback_end, None
    return None, None, None



def _aggregate_learning_data(
    user_id: int,
    start_date: Optional[date],
    end_date: Optional[date],
    stage: Optional[Stage],
) -> Dict:
    """
    Aggregate learning data in the given period.
    """
    logs_query = (
        LogEntry.query.join(Stage, LogEntry.stage_id == Stage.id)
        .filter(Stage.user_id == user_id)
        .order_by(LogEntry.log_date.asc(), LogEntry.id.asc())
    )
    if stage:
        logs_query = logs_query.filter(LogEntry.stage_id == stage.id)
    if start_date:
        logs_query = logs_query.filter(LogEntry.log_date >= start_date)
    if end_date:
        logs_query = logs_query.filter(LogEntry.log_date <= end_date)

    logs = logs_query.all()

    total_minutes = sum(int(log.actual_duration or 0) for log in logs)
    total_sessions = len(logs)

    daily_minutes: Dict[date, int] = defaultdict(int)
    mood_sum = 0
    mood_count = 0
    task_counter: Counter[str] = Counter()
    category_minutes: Dict[str, int] = defaultdict(int)

    subcategory_ids = {
        log.subcategory_id for log in logs if log.subcategory_id is not None
    }
    subcategory_map: Dict[int, SubCategory] = {}
    if subcategory_ids:
        subcategory_map = {
            sub.id: sub
            for sub in SubCategory.query.filter(SubCategory.id.in_(subcategory_ids)).all()
        }

    for log in logs:
        minutes = int(log.actual_duration or 0)
        log_day = log.log_date
        daily_minutes[log_day] += minutes

        task_name = (log.task or '').strip() or '未命名任务'
        task_counter[task_name] += minutes

        if log.mood is not None:
            mood_sum += log.mood
            mood_count += 1

        category_name = '未分类'
        if log.subcategory_id and log.subcategory_id in subcategory_map:
            subcategory = subcategory_map[log.subcategory_id]
            if getattr(subcategory, 'category', None) and subcategory.category.name:
                category_name = subcategory.category.name
            elif subcategory.name:
                category_name = subcategory.name
        elif log.legacy_category:
            category_name = log.legacy_category
        category_minutes[category_name] += minutes

    average_mood = round(mood_sum / mood_count, 2) if mood_count else None

    efficiency_query = (
        DailyData.query.join(Stage, DailyData.stage_id == Stage.id)
        .filter(Stage.user_id == user_id)
        .order_by(DailyData.log_date.asc(), DailyData.id.asc())
    )
    if stage:
        efficiency_query = efficiency_query.filter(DailyData.stage_id == stage.id)
    if start_date:
        efficiency_query = efficiency_query.filter(DailyData.log_date >= start_date)
    if end_date:
        efficiency_query = efficiency_query.filter(DailyData.log_date <= end_date)

    efficiency_rows = efficiency_query.all()
    efficiency_values = [
        row.efficiency for row in efficiency_rows if row.efficiency is not None
    ]
    average_efficiency = (
        round(sum(efficiency_values) / len(efficiency_values), 2)
        if efficiency_values
        else None
    )

    daily_efficiency = {
        row.log_date: row.efficiency
        for row in efficiency_rows
        if row.efficiency is not None
    }

    all_days = sorted(set(daily_minutes.keys()) | set(daily_efficiency.keys()))
    daily_stats = [
        {
            'date': day.isoformat(),
            'duration_minutes': daily_minutes.get(day, 0),
            'efficiency': daily_efficiency.get(day),
        }
        for day in all_days
    ]

    category_stats = [
        {
            'name': name,
            'minutes': minutes,
            'hours': round(minutes / 60, 2),
            'percentage': round(minutes / max(total_minutes, 1) * 100, 1),
        }
        for name, minutes in sorted(
            category_minutes.items(), key=lambda item: item[1], reverse=True
        )
    ]

    top_tasks = [
        {
            'task': task,
            'minutes': minutes,
            'hours': round(minutes / 60, 2),
            'percentage': round(minutes / max(total_minutes, 1) * 100, 1),
        }
        for task, minutes in task_counter.most_common(5)
    ]

    active_days = len(daily_minutes)
    idle_days: List[str] = []
    if start_date and end_date:
        current = start_date
        while current <= end_date:
            if current not in daily_minutes:
                idle_days.append(current.isoformat())
            current += timedelta(days=1)

    return {
        'total_minutes': total_minutes,
        'total_hours': round(total_minutes / 60, 2) if total_minutes else 0,
        'total_sessions': total_sessions,
        'average_daily_minutes': (
            round(total_minutes / active_days, 2) if active_days else 0
        ),
        'average_efficiency': average_efficiency,
        'average_mood': average_mood,
        'daily_stats': daily_stats,
        'category_stats': category_stats,
        'top_tasks': top_tasks,
        'idle_days': idle_days,
    }




def _configure_gemini():
    if genai_sdk is None:
        raise AIPlannerError(
            "δ��װ google-genai SDK��"
            "���Ȱ� pip install google-genai �������ִ�� pip install -r requirements.txt ��װ����"
        )
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        raise AIPlannerError("未配置 Gemini API 密钥")
    client = _gemini_client_cache.get(api_key)
    if client is None:
        client = genai_sdk.Client(api_key=api_key)
        _gemini_client_cache.clear()
        _gemini_client_cache[api_key] = client
    model_name = current_app.config.get("GEMINI_MODEL", "gemini-2.5-flash")
    return client, model_name


def _format_period_label(scope: str, start: Optional[date], end: Optional[date]) -> str:
    scope_label = SCOPE_LABELS.get(scope, scope)
    if start and end:
        if start == end:
            return f"{scope_label}（{start.isoformat()}）"
        return f"{scope_label}（{start.isoformat()} 至 {end.isoformat()}）"
    return scope_label





def _build_analysis_prompt(
    scope: str,
    stats: Dict,
    stage: Optional[Stage],
    period_label: str,
) -> str:
    lines = [
        "请基于以下学习统计数据，输出结构清晰的中文分析总结（可包含小标题与项目符号）：",
        f"- 分析范围：{period_label}",
    ]
    if stage:
        lines.append(f"- 当前阶段：{stage.name}")

    lines.extend(
        [
            "- 总学习时长：约 {total_hours} 小时（{total_minutes} 分钟）".format(**stats),
            f"- 记录条数：{stats['total_sessions']}",
            f"- 平均每日时长：{stats['average_daily_minutes']} 分钟",
        ]
    )
    if stats.get("average_efficiency") is not None:
        lines.append(f"- 平均效率：{stats['average_efficiency']}")
    if stats.get("average_mood") is not None:
        lines.append(f"- 平均心情评分：{stats['average_mood']}")

    category_lines = [
        f"  • {item['name']}：{item['hours']} 小时，占比 {item['percentage']}%"
        for item in stats["category_stats"][:5]
    ]
    if category_lines:
        lines.append("- 主要投入方向（Top5）：\n" + "\n".join(category_lines))

    task_lines = [
        f"  • {item['task']}：{item['hours']} 小时，占比 {item['percentage']}%"
        for item in stats["top_tasks"]
        if item["task"]
    ]
    if task_lines:
        lines.append("- 高频任务概览：\n" + "\n".join(task_lines))

    if stats["idle_days"]:
        lines.append(
            "- 以下日期未记录学习，可结合计划指出原因或提醒："
            + ", ".join(stats["idle_days"])
        )

    lines.append(
        "请结合上述数据分别指出亮点、存在的薄弱环节以及可执行的改进建议，语气积极且真诚，帮助用户快速把握重点。"
    )
    return "\n".join(lines)


def _build_plan_prompt(
    scope: str,
    stats: Dict,
    stage: Optional[Stage],
    period_label: str,
    next_period_label: str,
) -> str:
    lines = [
        "请参考统计数据，为用户制定下一阶段的中文学习计划（结构清晰，可含项目符号）：",
        f"- 当前复盘范围：{period_label}",
        f"- 规划目标范围：{next_period_label}",
    ]
    if stage:
        lines.append(f"- 当前阶段：{stage.name}")

    lines.extend(
        [
            "- 本阶段累计时长：约 {total_hours} 小时".format(**stats),
            f"- 平均每日时长：{stats['average_daily_minutes']} 分钟",
        ]
    )
    if stats.get("average_efficiency") is not None:
        lines.append(f"- 当前平均效率：{stats['average_efficiency']}")

    if stats["category_stats"]:
        lines.append(
            "- 核心投入方向："
            + "；".join(
                [
                    f"{item['name']}（{item['hours']} 小时，占比 {item['percentage']}%）"
                    for item in stats["category_stats"][:5]
                ]
            )
        )

    lines.append(
        "请结合以上数据给出：1）核心目标 2）时间与节奏安排 3）重点任务/主题 4）效率或心态优化建议，可适当引用数据佐证，鼓励用户保持动力。"
    )
    if scope == "day":
        lines.append("优先安排次日的关键任务顺序与时长分配，同时给出复盘建议。")
    elif scope == "week":
        lines.append("规划需覆盖每周 3-4 个重点，明确里程碑节点与缓冲时间。")
    elif scope == "month":
        lines.append("需拆分到周维度的阶段目标，并提示如何跟踪进展。")
    elif scope == "stage":
        lines.append("围绕阶段性目标给出持续推进与承上启下的建议，如有下一阶段名称可提前呼应。")

    lines.append("最后给出一句鼓励性的总结语。")
    return "\n".join(lines)


def _call_gemini(prompt: str) -> str:
    client, model_name = _configure_gemini()
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
    except GoogleAPIError as exc:
        detail = getattr(exc, "message", str(exc))
        raise AIPlannerError(
            f"调用 Gemini 接口失败：{detail}（模型：{model_name}）"
        ) from exc
    except Exception as exc:
        raise AIPlannerError(f"生成内容失败，请稍后重试：{exc}") from exc

    if not response or not getattr(response, "text", None):
        raise AIPlannerError("未能生成有效的模型输出")
    return response.text.strip()


def _save_insight(
    user_id: int,
    insight_type: str,
    scope: str,
    scope_reference: Optional[int],
    start_date: Optional[date],
    end_date: Optional[date],
    next_start: Optional[date],
    next_end: Optional[date],
    snapshot: Dict,
    output_text: str,
) -> AIInsight:
    insight = AIInsight(
        user_id=user_id,
        insight_type=insight_type,
        scope=scope,
        scope_reference=scope_reference,
        start_date=start_date,
        end_date=end_date,
        next_start_date=next_start,
        next_end_date=next_end,
        input_snapshot=snapshot,
        output_text=output_text,
    )
    db.session.add(insight)
    db.session.commit()
    return insight


def generate_analysis(
    user_id: int,
    scope: str,
    date_str: Optional[str] = None,
    stage_id: Optional[int] = None,
) -> Dict:
    start, end, stage = _get_date_range_for_scope(scope, date_str, stage_id, user_id)
    stats = _aggregate_learning_data(user_id, start, end, stage)
    period_label = _format_period_label(scope, start, end)
    prompt = _build_analysis_prompt(scope, stats, stage, period_label)
    output_text = _call_gemini(prompt)
    insight = _save_insight(
        user_id=user_id,
        insight_type="analysis",
        scope=scope,
        scope_reference=stage_id if scope == "stage" else None,
        start_date=start,
        end_date=end,
        next_start=None,
        next_end=None,
        snapshot={
            "scope": scope,
            "period_label": period_label,
            "stats": stats,
            "stage": stage.name if stage else None,
        },
        output_text=output_text,
    )
    return {
        "insight_id": insight.id,
        "text": output_text,
        "generated_at": insight.created_at.isoformat(),
        "period_label": period_label,
    }


def generate_plan(
    user_id: int,
    scope: str,
    date_str: Optional[str] = None,
    stage_id: Optional[int] = None,
) -> Dict:
    start, end, stage = _get_date_range_for_scope(scope, date_str, stage_id, user_id)
    stats = _aggregate_learning_data(user_id, start, end, stage)
    next_start, next_end, next_stage_name = _get_next_range(
        scope, start, end, stage, user_id
    )
    period_label = _format_period_label(scope, start, end)
    next_period_label = _format_period_label(scope, next_start, next_end)
    if scope == "stage" and next_stage_name:
        next_period_label = f"阶段：{next_stage_name}"
    prompt = _build_plan_prompt(
        scope, stats, stage, period_label, next_period_label or "后续阶段"
    )
    output_text = _call_gemini(prompt)
    insight = _save_insight(
        user_id=user_id,
        insight_type="plan",
        scope=scope,
        scope_reference=stage_id if scope == "stage" else None,
        start_date=start,
        end_date=end,
        next_start=next_start,
        next_end=next_end,
        snapshot={
            "scope": scope,
            "period_label": period_label,
            "next_period_label": next_period_label,
            "stats": stats,
            "stage": stage.name if stage else None,
            "next_stage": next_stage_name,
        },
        output_text=output_text,
    )
    return {
        "insight_id": insight.id,
        "text": output_text,
        "generated_at": insight.created_at.isoformat(),
        "period_label": period_label,
        "next_period_label": next_period_label,
    }


def list_history(
    user_id: int,
    limit: int = 20,
    offset: int = 0,
    scope: Optional[str] = None,
    insight_type: Optional[str] = None,
):
    query = (
        AIInsight.query.filter(AIInsight.user_id == user_id)
        .order_by(AIInsight.created_at.desc())
    )
    if scope:
        query = query.filter(AIInsight.scope == scope)
    if insight_type:
        query = query.filter(AIInsight.insight_type == insight_type)

    limit = max(1, limit)
    offset = max(0, offset)

    items = query.offset(offset).limit(limit).all()
    return [item.to_dict() for item in items]

