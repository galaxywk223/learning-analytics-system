from __future__ import annotations

from typing import Any, Dict, Optional

from flask import current_app

from app.models import AIInsight

from .aggregation import _aggregate_learning_data
from .briefing import _briefing_fallback, build_briefing_result
from .date_ranges import (
    _format_period_label,
    _get_date_range_for_scope,
    _get_next_range,
    _get_prev_range,
)
from .errors import AIPlannerError
from .persistence import _save_insight


def _resolve_briefing_context(
    user_id: int,
    scope: str,
    date_str: Optional[str],
    stage_id: Optional[int],
) -> Dict[str, Any]:
    start, end, stage = _get_date_range_for_scope(scope, date_str, stage_id, user_id)
    stats = _aggregate_learning_data(user_id, start, end, stage)
    prev_start, prev_end = _get_prev_range(scope, start, end)
    prev_stats = None
    if prev_start and prev_end and scope != "stage":
        prev_stats = _aggregate_learning_data(user_id, prev_start, prev_end, None)
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
    return {
        "start": start,
        "end": end,
        "stage": stage,
        "stats": stats,
        "prev_stats": prev_stats,
        "next_start": next_start,
        "next_end": next_end,
        "next_stage_name": next_stage_name,
        "period_label": period_label,
        "next_period_label": next_period_label,
        "next_days": next_days,
    }


def _generate_briefing_payload(
    user_id: int,
    scope: str,
    date_str: Optional[str] = None,
    stage_id: Optional[int] = None,
) -> Dict[str, Any]:
    context = _resolve_briefing_context(user_id, scope, date_str, stage_id)
    meta = {
        "scope": scope,
        "period_label": context["period_label"],
        "next_period_label": context["next_period_label"],
        "generated_at": None,
        "stage_name": context["stage"].name if context["stage"] else None,
        "next_stage_name": context["next_stage_name"],
        "next_days": context["next_days"],
    }
    try:
        result = build_briefing_result(meta, context["stats"], context["prev_stats"])
    except AIPlannerError:
        if current_app.config.get("AI_ENABLE_FALLBACK", True):
            result = _briefing_fallback(meta, context["stats"], context["prev_stats"])
        else:
            raise
    return {
        "briefing": result,
        "context": context,
    }


def _persist_briefing_insight(
    *,
    user_id: int,
    insight_type: str,
    scope: str,
    stage_id: Optional[int],
    briefing: Dict[str, Any],
    context: Dict[str, Any],
    output_text: str,
):
    snapshot = {
        "workflow_type": "briefing",
        "scope": scope,
        "period_label": briefing["meta"].get("period_label"),
        "next_period_label": briefing["meta"].get("next_period_label"),
        "stats": context["stats"],
        "prev_stats": context["prev_stats"],
        "stage": context["stage"].name if context["stage"] else None,
        "next_stage": context["next_stage_name"],
        "diagnosis": briefing.get("diagnosis"),
        "battle_plan": briefing.get("battle_plan"),
        "evidence": briefing.get("evidence"),
        "narrative": briefing.get("narrative"),
        "core_judgement": briefing.get("diagnosis", {}).get("core_judgement"),
        "status_level": briefing.get("diagnosis", {}).get("status_level"),
    }
    return _save_insight(
        user_id=user_id,
        insight_type=insight_type,
        scope=scope,
        scope_reference=stage_id if scope == "stage" else None,
        start_date=context["start"],
        end_date=context["end"],
        next_start=context["next_start"],
        next_end=context["next_end"],
        snapshot=snapshot,
        output_text=output_text,
    )


def generate_briefing(
    user_id: int,
    scope: str,
    date_str: Optional[str] = None,
    stage_id: Optional[int] = None,
) -> Dict[str, Any]:
    payload = _generate_briefing_payload(user_id, scope, date_str, stage_id)
    briefing = payload["briefing"]
    insight = _persist_briefing_insight(
        user_id=user_id,
        insight_type="briefing",
        scope=scope,
        stage_id=stage_id,
        briefing=briefing,
        context=payload["context"],
        output_text=briefing["narrative"]["full_markdown"],
    )
    briefing["meta"]["generated_at"] = insight.created_at.isoformat()
    briefing["insight_id"] = insight.id
    return briefing


def generate_analysis(
    user_id: int,
    scope: str,
    date_str: Optional[str] = None,
    stage_id: Optional[int] = None,
) -> Dict:
    payload = _generate_briefing_payload(user_id, scope, date_str, stage_id)
    briefing = payload["briefing"]
    output_text = briefing["narrative"]["analysis_markdown"]
    insight = _persist_briefing_insight(
        user_id=user_id,
        insight_type="analysis",
        scope=scope,
        stage_id=stage_id,
        briefing=briefing,
        context=payload["context"],
        output_text=output_text,
    )
    return {
        "insight_id": insight.id,
        "text": output_text,
        "generated_at": insight.created_at.isoformat(),
        "period_label": briefing["meta"]["period_label"],
        "briefing": briefing,
    }


def generate_plan(
    user_id: int,
    scope: str,
    date_str: Optional[str] = None,
    stage_id: Optional[int] = None,
) -> Dict:
    payload = _generate_briefing_payload(user_id, scope, date_str, stage_id)
    briefing = payload["briefing"]
    output_text = briefing["narrative"]["plan_markdown"]
    insight = _persist_briefing_insight(
        user_id=user_id,
        insight_type="plan",
        scope=scope,
        stage_id=stage_id,
        briefing=briefing,
        context=payload["context"],
        output_text=output_text,
    )
    return {
        "insight_id": insight.id,
        "text": output_text,
        "generated_at": insight.created_at.isoformat(),
        "period_label": briefing["meta"]["period_label"],
        "next_period_label": briefing["meta"]["next_period_label"],
        "briefing": briefing,
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


__all__ = ["generate_briefing", "generate_analysis", "generate_plan", "list_history"]
