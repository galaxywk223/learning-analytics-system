from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from flask import current_app

from app import db
from app.models import AIChatMessage, AIChatSession

from .chat_context import build_default_chat_context, build_global_chat_context, build_requested_modules, normalize_requested_modules, normalize_requested_windows
from .errors import AIPlannerError
from .llm_client import _call_qwen

_VISIBLE_HISTORY_LIMIT = 12


def _extract_json_block(raw_text: str) -> dict[str, Any]:
    cleaned = (raw_text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("planner pass did not return a JSON object")
    return json.loads(cleaned[start : end + 1])


def _session_title_from_message(content: str) -> str:
    compact = re.sub(r"\s+", " ", (content or "").strip())
    if not compact:
        return "新对话"
    return compact[:40]


def _serialize_history(messages: list[AIChatMessage]) -> list[dict[str, Any]]:
    return [
        {
            "role": item.role,
            "content": item.content,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in messages
    ]


def _planner_pass_prompt(
    *,
    user_question: str,
    visible_history: list[dict[str, Any]],
    default_context: dict[str, Any],
) -> str:
    return "\n".join(
        [
            "你是一个隐藏的查询规划器。不要直接回答用户问题。",
            "你只负责判断：现有上下文是否足够回答，如果不够，还需要哪些补充模块。",
            "严格返回 JSON，不要输出 markdown，不要输出解释。",
            'JSON schema: {"decision":"answer_with_current_context|need_more_context","needed_modules":["trend_daily_detail"],"time_windows":["current_week"],"focus":"一句话说明关注点","answer_strategy":"一句话说明回答策略"}',
            "允许的 needed_modules 仅限：trend_daily_detail, trend_weekly_detail, forecast_detail, category_duration_detail, category_efficiency_detail, task_focus_detail, stage_timeline_detail, countdown_detail, recent_ai_history_detail",
            "允许的 time_windows 仅限：current_day, current_week, previous_week, current_month, previous_month, last_30_days, last_90_days, current_stage, previous_stage",
            "如果现有上下文已经够用，needed_modules 和 time_windows 都返回空数组。",
            f"用户问题：{user_question}",
            f"可见对话历史：{json.dumps(visible_history, ensure_ascii=False)}",
            f"默认上下文：{json.dumps(default_context, ensure_ascii=False)}",
        ]
    )


def _answer_pass_prompt(
    *,
    user_question: str,
    visible_history: list[dict[str, Any]],
    default_context: dict[str, Any],
    requested_modules: dict[str, Any],
    answer_strategy: str,
) -> str:
    return "\n".join(
        [
            "你现在直接像网页大模型那样回复用户。",
            "要求：",
            "1. 先直接回答问题，不要先讲方法论。",
            "2. 少空话，多引用事实、分类、趋势、阶段、倒计时和数字。",
            "3. 不要复述整包上下文，不要把所有模块逐条念一遍。",
            "4. 可以自然分段，但不要输出 JSON。",
            "5. 如果需要建议，给 2-4 条最关键动作即可。",
            "6. 不要提你经历了内部两轮判断，也不要暴露模块名。",
            f"回答策略：{answer_strategy or '直接回答，并只补足最关键的事实依据。'}",
            f"用户问题：{user_question}",
            f"可见对话历史：{json.dumps(visible_history, ensure_ascii=False)}",
            f"默认上下文：{json.dumps(default_context, ensure_ascii=False)}",
            f"补充上下文：{json.dumps(requested_modules, ensure_ascii=False)}",
        ]
    )


def _fallback_chat_reply(
    *,
    user_question: str,
    context_bundle: dict[str, Any],
) -> str:
    default_context = context_bundle["default_context"]
    metrics = default_context["overview_metrics"]
    categories = default_context.get("category_focus") or []
    countdown_context = default_context.get("countdown_context") or {}
    comparison = default_context.get("comparison") or {}
    total_hours_delta = comparison.get("total_hours", {}).get("delta_pct")
    top_focus = "、".join(
        f"{item['name']} {item['hours']}h" for item in categories[:3]
    ) or "当前没有足够的分类投入数据"
    countdown_titles = [
        item.get("title")
        for item in (countdown_context.get("sprint_events") or [])[:2]
        if item.get("title")
    ]
    countdown_line = (
        f"你当前最近的冲刺节点是 {'、'.join(countdown_titles)}。"
        if countdown_titles
        else "当前没有特别近的冲刺节点。"
    )
    delta_line = ""
    if total_hours_delta is not None:
        delta_line = f"和上一周期相比，总时长变化 {total_hours_delta:+.1f}%。"
    return (
        f"我先直接回答你这个问题：{user_question}\n\n"
        f"按你当前这段数据看，最值得先盯住的是总时长 {metrics.get('total_hours', 0)}h、平均效率 "
        f"{metrics.get('average_efficiency', '--')}、活跃率 "
        f"{round(float(metrics.get('active_ratio') or 0) * 100, 1)}%。{delta_line}\n\n"
        f"你最近的主要投入方向是：{top_focus}。{countdown_line}\n\n"
        "如果你要我继续往下判断，我建议你接着问得更具体一点，比如“我下周到底该砍掉什么”或者"
        "“为什么我最近效率掉了”。这样我能直接沿着这个问题往下给你结论。"
    )


def _resolve_generation_mode(model_name: str | None, used_fallback: bool) -> tuple[str, str]:
    if used_fallback:
        return "rule_fallback", "规则兜底"
    return "llm_enhanced", "LLM增强"


def _get_session_or_raise(user_id: int, session_id: int) -> AIChatSession:
    session = AIChatSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        raise AIPlannerError("会话不存在或无权访问")
    return session


def list_chat_sessions(user_id: int) -> list[dict[str, Any]]:
    sessions = (
        AIChatSession.query.filter(AIChatSession.user_id == user_id)
        .order_by(AIChatSession.last_message_at.desc(), AIChatSession.created_at.desc())
        .all()
    )
    return [session.to_dict() for session in sessions]


def list_chat_messages(user_id: int, session_id: int) -> dict[str, Any]:
    session = _get_session_or_raise(user_id, session_id)
    messages = [message.to_dict() for message in session.messages.all()]
    return {"session": session.to_dict(), "messages": messages}


def create_chat_message(
    user_id: int,
    *,
    session_id: int | None,
    scope: str,
    date_str: str | None,
    stage_id: int | None,
    content: str,
) -> dict[str, Any]:
    question = str(content or "").strip()
    if not question:
        raise AIPlannerError("content 不能为空")

    session = _get_session_or_raise(user_id, session_id) if session_id else None
    if session is None:
        session = AIChatSession(
            user_id=user_id,
            title=_session_title_from_message(question),
            scope=scope,
            scope_reference=stage_id if scope == "stage" else None,
            date_reference=None if scope == "stage" else context_date(date_str),
        )
        db.session.add(session)
        db.session.flush()

    session.scope = scope
    session.scope_reference = stage_id if scope == "stage" else None
    session.date_reference = None if scope == "stage" else context_date(date_str)

    visible_history_messages = (
        AIChatMessage.query.filter(AIChatMessage.session_id == session.id)
        .order_by(AIChatMessage.created_at.desc())
        .limit(_VISIBLE_HISTORY_LIMIT)
        .all()
    )
    visible_history = _serialize_history(list(reversed(visible_history_messages)))

    if scope == "global":
        context_bundle = build_global_chat_context(user_id, session_id=session.id)
    else:
        context_bundle = build_default_chat_context(
            user_id,
            scope,
            date_str,
            stage_id,
            session_id=session.id,
        )
    default_context = context_bundle["default_context"]

    planner_prompt = _planner_pass_prompt(
        user_question=question,
        visible_history=visible_history,
        default_context=default_context,
    )

    planner_result: dict[str, Any] = {
        "decision": "answer_with_current_context",
        "needed_modules": [],
        "focus": question[:80],
        "answer_strategy": "直接回答，并引用最关键的事实证据。",
    }
    planner_failed = False
    try:
        planner_raw = _call_qwen(planner_prompt)
        planner_result.update(_extract_json_block(planner_raw))
    except Exception:
        planner_failed = True
        current_app.logger.warning("AI chat planner pass fell back for user %s", user_id)

    requested_module_names = normalize_requested_modules(
        list(planner_result.get("needed_modules") or [])
    )
    requested_window_names = normalize_requested_windows(
        list(planner_result.get("time_windows") or [])
    )
    requested_modules = build_requested_modules(
        user_id,
        context_bundle,
        requested_module_names,
        requested_windows=requested_window_names,
        session_id=session.id,
    )

    model_name = current_app.config.get("QWEN_MODEL", "qwen-plus-2025-07-28")
    answer_prompt = _answer_pass_prompt(
        user_question=question,
        visible_history=visible_history,
        default_context=default_context,
        requested_modules=requested_modules,
        answer_strategy=str(planner_result.get("answer_strategy") or ""),
    )

    used_fallback = False
    try:
        assistant_content = _call_qwen(answer_prompt)
    except Exception:
        assistant_content = _fallback_chat_reply(
            user_question=question,
            context_bundle=context_bundle,
        )
        used_fallback = True

    if planner_failed:
        used_fallback = used_fallback or False

    generation_mode, generation_label = _resolve_generation_mode(model_name, used_fallback)
    now = datetime.utcnow()

    user_message = AIChatMessage(
        session_id=session.id,
        user_id=user_id,
        role="user",
        content=question,
        scope=scope,
        scope_reference=stage_id if scope == "stage" else None,
        date_reference=None if scope == "stage" else context_date(date_str),
        generation_mode=None,
        model_name=None,
        meta_snapshot={
            "period_label": context_bundle["meta"]["period_label"],
        },
        created_at=now,
    )
    assistant_message = AIChatMessage(
        session_id=session.id,
        user_id=user_id,
        role="assistant",
        content=assistant_content,
        scope=scope,
        scope_reference=stage_id if scope == "stage" else None,
        date_reference=None if scope == "stage" else context_date(date_str),
        generation_mode=generation_mode,
        model_name=None if used_fallback else model_name,
        meta_snapshot={
            "generation_label": generation_label,
            "period_label": context_bundle["meta"]["period_label"],
            "next_period_label": context_bundle["meta"]["next_period_label"],
            "used_modules": requested_module_names,
            "used_windows": requested_window_names,
            "focus": planner_result.get("focus"),
        },
        created_at=now,
    )
    db.session.add(user_message)
    db.session.add(assistant_message)
    session.last_message_at = now
    session.updated_at = now
    if session.title == "新对话":
        session.title = _session_title_from_message(question)
    db.session.commit()

    return {
        "session": session.to_dict(),
        "user_message": user_message.to_dict(),
        "assistant_message": assistant_message.to_dict(),
        "meta": {
            "generation_mode": generation_mode,
            "generation_label": generation_label,
            "model_name": None if used_fallback else model_name,
            "used_modules": requested_module_names,
            "used_windows": requested_window_names,
            "scope": scope,
            "period_label": context_bundle["meta"]["period_label"],
        },
    }


def context_date(date_str: str | None):
    if not date_str:
        return None
    return datetime.strptime(date_str, "%Y-%m-%d").date()
