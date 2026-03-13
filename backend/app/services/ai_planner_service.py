"""
Facade for AI planner service.

The original monolith has been modularized under app.services.ai_planner;
this file keeps the public API stable for existing imports.
"""

from __future__ import annotations

from app.services.ai_planner import (  # type: ignore[F401]
    AIPlannerError,
    SCOPE_LABELS,
    _aggregate_learning_data,
    _build_analysis_prompt,
    _build_countdown_context,
    _build_plan_prompt,
    _call_qwen,
    _compute_efficiency_baseline,
    _configure_qwen,
    _fallback_analysis_text,
    _fallback_plan_text,
    _format_period_label,
    _get_date_range_for_scope,
    _get_next_range,
    _get_prev_range,
    _parse_date,
    _save_insight,
    generate_analysis,
    generate_briefing,
    generate_plan,
    list_history,
)

__all__ = [
    "AIPlannerError",
    "SCOPE_LABELS",
    "_parse_date",
    "_get_date_range_for_scope",
    "_get_next_range",
    "_get_prev_range",
    "_format_period_label",
    "_build_countdown_context",
    "_compute_efficiency_baseline",
    "_aggregate_learning_data",
    "_build_analysis_prompt",
    "_build_plan_prompt",
    "_fallback_analysis_text",
    "_fallback_plan_text",
    "_configure_qwen",
    "_call_qwen",
    "_save_insight",
    "generate_briefing",
    "generate_analysis",
    "generate_plan",
    "list_history",
]
