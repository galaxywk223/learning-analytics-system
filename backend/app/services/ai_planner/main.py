from __future__ import annotations

from typing import Dict, Optional

from flask import current_app

from app.models import AIInsight

from .aggregation import _aggregate_learning_data
from .date_ranges import (
    _format_period_label,
    _get_date_range_for_scope,
    _get_next_range,
    _get_prev_range,
)
from .errors import AIPlannerError
from .llm_client import _call_qwen
from .persistence import _save_insight
from .prompts import (
    _build_analysis_prompt,
    _build_plan_prompt,
    _fallback_analysis_text,
    _fallback_plan_text,
)


def generate_analysis(
    user_id: int,
    scope: str,
    date_str: Optional[str] = None,
    stage_id: Optional[int] = None,
) -> Dict:
    start, end, stage = _get_date_range_for_scope(scope, date_str, stage_id, user_id)
    stats = _aggregate_learning_data(user_id, start, end, stage)
    # 上一周期（仅限日/周/月）
    prev_start, prev_end = _get_prev_range(scope, start, end)
    prev_stats = None
    if prev_start and prev_end and scope != "stage":
        prev_stats = _aggregate_learning_data(user_id, prev_start, prev_end, None)
    period_label = _format_period_label(scope, start, end)
    prompt = _build_analysis_prompt(scope, stats, stage, period_label, prev_stats)
    try:
        output_text = _call_qwen(prompt)
    except AIPlannerError:
        # 兜底：允许用模板生成，避免前端空结果
        if current_app.config.get("AI_ENABLE_FALLBACK", True):
            output_text = _fallback_analysis_text(scope, stats, period_label, prev_stats)
        else:
            raise
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
    next_days = (
        (next_end - next_start).days + 1 if next_start and next_end else None
    )
    prompt = _build_plan_prompt(
        scope, stats, stage, period_label, next_period_label or "后续阶段", next_days
    )
    try:
        output_text = _call_qwen(prompt)
    except AIPlannerError:
        if current_app.config.get("AI_ENABLE_FALLBACK", True):
            output_text = _fallback_plan_text(
                scope,
                stats,
                period_label,
                next_period_label or "后续阶段",
                next_days,
            )
        else:
            raise
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


__all__ = ["generate_analysis", "generate_plan", "list_history"]
