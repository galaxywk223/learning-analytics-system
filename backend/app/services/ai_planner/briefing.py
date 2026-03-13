from __future__ import annotations

import json
import math
import re
from datetime import date
from typing import Any, Dict, Optional

from . import llm_client
from .errors import AIPlannerError


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _format_hours(minutes: float) -> str:
    return f"{round(minutes / 60.0, 1)}h"


def _pick_top_category(stats: Dict[str, Any]) -> Dict[str, Any]:
    categories = stats.get("category_stats") or []
    return categories[0] if categories else {"name": "当前重点方向", "percentage": 0, "hours": 0}


def _pct_change(current: float, previous: float | None) -> float | None:
    if previous is None or previous == 0:
        return None
    return round(((current - previous) / previous) * 100, 1)


def _infer_pressure_context(stats: Dict[str, Any]) -> str:
    countdown = stats.get("countdown_context") or {}
    return str(countdown.get("pressure_phase") or "balanced")


def _build_metric_snapshot(stats: Dict[str, Any], prev_stats: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    baseline = stats.get("efficiency_baseline") or {}
    current_hours = _safe_float(stats.get("total_hours"))
    previous_hours = _safe_float((prev_stats or {}).get("total_hours"), default=0.0)
    current_efficiency = (
        None if stats.get("average_efficiency") is None else _safe_float(stats.get("average_efficiency"))
    )
    previous_efficiency = (
        None
        if not prev_stats or prev_stats.get("average_efficiency") is None
        else _safe_float(prev_stats.get("average_efficiency"))
    )
    return {
        "total_hours": round(current_hours, 2),
        "total_sessions": int(stats.get("total_sessions") or 0),
        "average_daily_minutes": round(_safe_float(stats.get("average_daily_minutes")), 2),
        "average_efficiency": current_efficiency,
        "average_mood": stats.get("average_mood"),
        "active_ratio": stats.get("active_ratio"),
        "active_days": int(stats.get("active_days") or 0),
        "total_days": int(stats.get("total_days") or 0),
        "streak_current": int(stats.get("streak_current") or 0),
        "streak_longest": int(stats.get("streak_longest") or 0),
        "vs_previous": {
            "hours_pct": _pct_change(current_hours, previous_hours if prev_stats else None),
            "efficiency_delta": None
            if current_efficiency is None or previous_efficiency is None
            else round(current_efficiency - previous_efficiency, 2),
        },
        "efficiency_baseline": {
            "all_time_avg": baseline.get("all_time_avg"),
            "last_30d_avg": baseline.get("last_30d_avg"),
            "last_30d_peak": baseline.get("last_30d_peak"),
        },
    }


def _build_evidence_payload(
    scope: str,
    period_label: str,
    next_period_label: str,
    stats: Dict[str, Any],
    prev_stats: Optional[Dict[str, Any]],
    stage_name: Optional[str],
) -> Dict[str, Any]:
    countdown = stats.get("countdown_context") or {}
    return {
        "scope": scope,
        "stage_name": stage_name,
        "period_label": period_label,
        "next_period_label": next_period_label,
        "metrics": _build_metric_snapshot(stats, prev_stats),
        "category_focus": (stats.get("category_stats") or [])[:5],
        "task_focus": (stats.get("top_tasks") or [])[:5],
        "cadence": {
            "weekday_stats": (stats.get("weekday_stats") or [])[:7],
            "hour_stats": [
                item
                for item in (stats.get("hour_stats") or [])
                if _safe_float(item.get("minutes")) > 0
            ][:6],
            "idle_days": (stats.get("idle_days") or [])[:10],
        },
        "countdown_context": {
            "pressure_phase": countdown.get("pressure_phase"),
            "sprint_events": (countdown.get("sprint_events") or [])[:3],
            "recovery_events": (countdown.get("recovery_events") or [])[:3],
            "timeline": (countdown.get("timeline") or [])[:6],
        },
    }


def _status_from_score(score: int) -> str:
    if score >= 72:
        return "green"
    if score >= 50:
        return "yellow"
    return "red"


def _build_rule_based_diagnosis(
    scope: str,
    stats: Dict[str, Any],
    prev_stats: Optional[Dict[str, Any]],
    period_label: str,
) -> Dict[str, Any]:
    baseline = stats.get("efficiency_baseline") or {}
    current_hours = _safe_float(stats.get("total_hours"))
    previous_hours = _safe_float((prev_stats or {}).get("total_hours"), default=0.0)
    current_efficiency = _safe_float(stats.get("average_efficiency"), default=0.0)
    previous_efficiency = (
        _safe_float((prev_stats or {}).get("average_efficiency"), default=0.0)
        if prev_stats and prev_stats.get("average_efficiency") is not None
        else None
    )
    recent_efficiency = baseline.get("last_30d_avg")
    all_time_efficiency = baseline.get("all_time_avg")
    active_ratio = _safe_float(stats.get("active_ratio"), default=0.0)
    streak_current = int(stats.get("streak_current") or 0)
    top_category = _pick_top_category(stats)
    pressure = _infer_pressure_context(stats)

    score = 58
    key_signals: list[str] = []
    risks: list[str] = []
    opportunities: list[str] = []

    hour_delta_pct = _pct_change(current_hours, previous_hours if prev_stats else None)
    eff_delta = (
        None
        if previous_efficiency is None or stats.get("average_efficiency") is None
        else round(current_efficiency - previous_efficiency, 2)
    )

    if hour_delta_pct is not None:
        if hour_delta_pct >= 15:
            score += 6
            key_signals.append(f"本周期投入较上一周期明显抬升（{hour_delta_pct:+.1f}%），说明执行意愿在增强。")
        elif hour_delta_pct <= -15:
            score -= 8
            risks.append(f"本周期投入较上一周期回落明显（{hour_delta_pct:+.1f}%），需要排查节奏掉线还是战术回撤。")

    if recent_efficiency is not None and stats.get("average_efficiency") is not None:
        eff_gap = round(current_efficiency - _safe_float(recent_efficiency), 2)
        if eff_gap >= 0.4:
            score += 8
            key_signals.append(f"当前效率高于近30天均值 {eff_gap:+.2f}，属于质量在线的输出。")
        elif eff_gap <= -0.4:
            score -= 10
            risks.append(f"当前效率低于近30天均值 {eff_gap:.2f}，警惕低效堆时长。")

    if all_time_efficiency is not None and stats.get("average_efficiency") is not None:
        full_gap = round(current_efficiency - _safe_float(all_time_efficiency), 2)
        if full_gap >= 0.3:
            opportunities.append("当前效率已压过历史均值，说明你具备继续加码的空间。")

    if active_ratio >= 0.8:
        score += 6
        key_signals.append(f"活跃率 {round(active_ratio * 100, 1)}%，执行连续性不错。")
    elif active_ratio <= 0.45:
        score -= 8
        risks.append(f"活跃率只有 {round(active_ratio * 100, 1)}%，当前最大问题是节奏断档。")

    if streak_current >= 5:
        score += 4
        opportunities.append(f"当前已经连续打卡 {streak_current} 天，可以利用惯性继续抬强度。")

    top_ratio = _safe_float(top_category.get("percentage"))
    if top_ratio >= 65:
        if pressure == "sprint":
            score += 4
            key_signals.append(
                f"当前 {top_category.get('name')} 占比 {top_ratio:.1f}%，在冲刺窗口内属于合理的单点突破。"
            )
        else:
            score -= 7
            risks.append(
                f"{top_category.get('name')} 占比已经到 {top_ratio:.1f}%，存在结构性失衡，容易形成战术逃避。"
            )
    elif top_ratio >= 45:
        opportunities.append(
            f"{top_category.get('name')} 已形成主轴，但仍保留了调整空间，可以继续做资源倾斜。"
        )

    if (
        stats.get("average_efficiency") is not None
        and active_ratio >= 0.8
        and recent_efficiency is not None
        and current_efficiency < _safe_float(recent_efficiency) - 0.6
    ):
        score -= 7
        risks.append("活跃率很高但效率在下滑，像是在靠意志力硬顶，已经有疲劳堆积信号。")

    if pressure == "cooldown":
        key_signals.append("当前处于回血窗口，允许效率暂时回落，但不适合彻底散掉。")
    elif pressure == "sprint":
        key_signals.append("当前处于冲刺窗口，评价重点应从“均衡”切换到“是否打穿核心目标”。")

    score = max(24, min(92, score))
    status_level = _status_from_score(score)

    if status_level == "green":
        core_judgement = "这不是普通稳定期，而是可以继续压强度的进攻窗口。"
    elif status_level == "yellow":
        core_judgement = "节奏还没崩，但已经出现结构性噪音，必须先纠偏再加码。"
    else:
        core_judgement = "现在最大的问题不是不努力，而是策略失焦和效率泄漏。"

    if not key_signals:
        key_signals.append(f"{period_label} 内的投入还不够形成强势趋势，当前更需要先把节奏做稳。")
    if not risks:
        risks.append("没有看到明显的红色风险，但仍要防止任务切换过碎。")
    if not opportunities:
        opportunities.append("当前最值得放大的，是把已经有效的主轴学科继续做深。")

    if pressure == "sprint":
        strategy_bias = "资源继续向最关键目标倾斜，允许战术性偏科。"
    elif pressure == "cooldown":
        strategy_bias = "先稳节奏和恢复效率，再逐步抬回强度。"
    elif top_ratio >= 55:
        strategy_bias = "保留主轴，但要给第二重点方向留出必要配比，防止结构失衡。"
    else:
        strategy_bias = "维持一主一辅的资源结构，避免面面俱到。"

    return {
        "core_judgement": core_judgement,
        "status_level": status_level,
        "key_signals": key_signals[:5],
        "risks": risks[:4],
        "opportunities": opportunities[:3],
        "strategy_bias": strategy_bias,
        "score": score,
        "period_label": period_label,
        "supporting_metrics": {
            "hours_pct_change": hour_delta_pct,
            "efficiency_delta_vs_previous": eff_delta,
            "top_category": top_category.get("name"),
            "top_category_share": top_ratio,
            "pressure_phase": pressure,
        },
    }


def _build_rule_based_plan(
    scope: str,
    stats: Dict[str, Any],
    diagnosis: Dict[str, Any],
    next_period_label: str,
    next_days: Optional[int],
    next_stage_name: Optional[str],
) -> Dict[str, Any]:
    top_category = _pick_top_category(stats)
    categories = (stats.get("category_stats") or [])[:3]
    top_tasks = (stats.get("top_tasks") or [])[:3]
    pressure = _infer_pressure_context(stats)
    total_budget_hours = round(
        (_safe_float(stats.get("average_daily_minutes"), default=90.0) / 60.0)
        * float(next_days or (7 if scope != "stage" else 14)),
        1,
    )
    total_budget_hours = max(total_budget_hours, 6.0)

    if pressure == "sprint":
        main_objective = f"在 {next_period_label} 内优先打穿 {top_category.get('name')} 的关键结果。"
        rhythm = [
            "前半程集中清主目标，后半程只做巩固与查漏。",
            "高效时段只给最关键任务，不把注意力浪费在低价值补丁上。",
            "每 2 天做一次小复盘，确认是否真的在推进主目标。",
        ]
    elif pressure == "cooldown":
        main_objective = f"在 {next_period_label} 内先把效率和节奏拉回可持续区间。"
        rhythm = [
            "前 1/3 周期先稳住作息和连续性，再逐步提高强度。",
            "重建固定学习时段，避免全天碎片式学习。",
            "每次学习后留 10 分钟收束，防止重新陷入低效堆时长。",
        ]
    else:
        main_objective = f"在 {next_period_label} 内把主轴任务做深，同时维持结构稳定。"
        rhythm = [
            "先保主轴，再给第二重点方向分配稳定时段。",
            "每周中段检查一次投入结构，避免偏离重点。",
            "用高效时段推进难任务，用低负荷时段处理整理和复盘。",
        ]

    secondary_objectives = [
        "把高频任务从“做了很多”切换成“真正产出结果”。",
        "守住连续性，避免再次出现节奏断档。",
        "把效率表现维持在近30天均值之上，而不是只堆时长。",
    ]

    if diagnosis.get("status_level") == "red":
        secondary_objectives[0] = "先止损：砍掉低收益任务，把资源重新收回主轴。"

    if categories:
        base_allocations = [55, 30, 15] if pressure != "sprint" else [70, 20, 10]
        resource_allocation = []
        for index, item in enumerate(categories):
            allocation = base_allocations[index] if index < len(base_allocations) else 10
            resource_allocation.append(
                {
                    "target": item.get("name"),
                    "allocation_pct": allocation,
                    "reason": "主轴加码" if index == 0 else "保持结构稳定",
                }
            )
    else:
        resource_allocation = [
            {"target": "主轴任务", "allocation_pct": 60, "reason": "确保关键结果先兑现"},
            {"target": "次重点任务", "allocation_pct": 25, "reason": "防止结构失衡"},
            {"target": "复盘与整理", "allocation_pct": 15, "reason": "沉淀与纠偏"},
        ]

    critical_tasks = []
    for item in top_tasks:
        critical_tasks.append(
            {
                "task": item.get("task"),
                "focus": "把任务拆到可验证的小结果，优先完成最难的 20%。",
                "guardrail": "完成后立即记录结果，不允许只刷时长不收口。",
            }
        )
    if not critical_tasks:
        critical_tasks.append(
            {
                "task": "主轴学习任务",
                "focus": "围绕当前最重要目标推进，不做无关扩展。",
                "guardrail": "每次学习结束必须留下可验证产出。",
            }
        )

    anti_patterns = [
        "为了看起来努力而拉长低质量时长。",
        "主任务没推进，却把精力耗在整理、选题和重复刷熟练区。",
        "阶段压力变大时反而去做最熟悉、最不痛的任务。",
    ]
    if pressure == "cooldown":
        anti_patterns[0] = "把回血期当成彻底摆烂窗口，导致节奏重新断掉。"

    next_review_point = (
        f"{next_stage_name} 开始前复盘一次" if scope == "stage" and next_stage_name else "执行 3 天后做第一次偏差检查"
    )

    return {
        "main_objective": main_objective,
        "secondary_objectives": secondary_objectives[:3],
        "resource_allocation": resource_allocation,
        "critical_tasks": critical_tasks[:3],
        "execution_rhythm": rhythm,
        "anti_patterns": anti_patterns[:3],
        "next_review_point": next_review_point,
        "budget_hours": total_budget_hours,
    }


def _render_narrative_markdown(
    meta: Dict[str, Any],
    diagnosis: Dict[str, Any],
    battle_plan: Dict[str, Any],
    evidence: Dict[str, Any],
) -> Dict[str, str]:
    period_label = meta.get("period_label") or "当前周期"
    next_period_label = meta.get("next_period_label") or "下一周期"
    metrics = evidence.get("metrics") or {}
    category_focus = evidence.get("category_focus") or []
    lines_analysis = [
        f"## 分析总结 · {period_label}",
        "",
        f"### 核心判断",
        f"- {diagnosis.get('core_judgement')}",
        f"- 当前状态：`{diagnosis.get('status_level')}`",
        "",
        "### 关键信号",
    ]
    lines_analysis.extend([f"- {item}" for item in diagnosis.get("key_signals") or []])
    lines_analysis.extend(["", "### 风险", *[f"- {item}" for item in diagnosis.get("risks") or []]])
    lines_analysis.extend(["", "### 机会", *[f"- {item}" for item in diagnosis.get("opportunities") or []]])
    lines_analysis.extend(
        [
            "",
            "### 证据",
            f"- 总时长：{metrics.get('total_hours', 0)}h",
            f"- 平均效率：{metrics.get('average_efficiency', '--')}",
            f"- 活跃率：{round(_safe_float(metrics.get('active_ratio')) * 100, 1)}%",
        ]
    )
    if category_focus:
        lines_analysis.append(
            "- 核心投入方向："
            + "；".join(
                [
                    f"{item.get('name')}（{item.get('hours')}h / {item.get('percentage')}%）"
                    for item in category_focus[:3]
                ]
            )
        )

    lines_plan = [
        f"## 规划建议 · {next_period_label}",
        "",
        "### 主目标",
        f"- {battle_plan.get('main_objective')}",
        "",
        "### 次目标",
    ]
    lines_plan.extend([f"- {item}" for item in battle_plan.get("secondary_objectives") or []])
    lines_plan.extend(["", "### 资源倾斜"])
    lines_plan.extend(
        [
            f"- {item.get('target')}：{item.get('allocation_pct')}% → {item.get('reason')}"
            for item in battle_plan.get("resource_allocation") or []
        ]
    )
    lines_plan.extend(["", "### 关键任务"])
    lines_plan.extend(
        [
            f"- **{item.get('task')}**：{item.get('focus')}；防错：{item.get('guardrail')}"
            for item in battle_plan.get("critical_tasks") or []
        ]
    )
    lines_plan.extend(["", "### 节奏"])
    lines_plan.extend([f"- {item}" for item in battle_plan.get("execution_rhythm") or []])
    lines_plan.extend(["", "### 反模式"])
    lines_plan.extend([f"- {item}" for item in battle_plan.get("anti_patterns") or []])
    lines_plan.extend(["", f"> 下一个复盘点：{battle_plan.get('next_review_point')}"])

    full_markdown = "\n".join(lines_analysis + ["", "---", ""] + lines_plan)
    return {
        "analysis_markdown": "\n".join(lines_analysis),
        "plan_markdown": "\n".join(lines_plan),
        "full_markdown": full_markdown,
    }


def _briefing_fallback(
    meta: Dict[str, Any],
    stats: Dict[str, Any],
    prev_stats: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    diagnosis = _build_rule_based_diagnosis(meta["scope"], stats, prev_stats, meta["period_label"])
    battle_plan = _build_rule_based_plan(
        meta["scope"],
        stats,
        diagnosis,
        meta["next_period_label"],
        meta.get("next_days"),
        meta.get("next_stage_name"),
    )
    evidence = _build_evidence_payload(
        meta["scope"],
        meta["period_label"],
        meta["next_period_label"],
        stats,
        prev_stats,
        meta.get("stage_name"),
    )
    narrative = _render_narrative_markdown(meta, diagnosis, battle_plan, evidence)
    return {
        "meta": {
            "scope": meta["scope"],
            "period_label": meta["period_label"],
            "next_period_label": meta["next_period_label"],
            "generated_at": meta.get("generated_at"),
            "stage_name": meta.get("stage_name"),
        },
        "diagnosis": diagnosis,
        "battle_plan": battle_plan,
        "evidence": evidence,
        "narrative": narrative,
    }


def _build_structured_briefing_prompt(fallback_briefing: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "你是一位锋利直接的学习策略参谋。",
            "请基于给定证据，把当前周期复盘与下一周期作战方案输出为严格 JSON。",
            "要求：",
            "1. 语气直接，不要鸡汤。",
            "2. 保持字段完整，不要缺字段。",
            "3. 所有数组元素都必须是简洁中文句子。",
            "4. 只输出 JSON，不要输出 Markdown，不要解释。",
            "5. diagnosis.status_level 只能是 green/yellow/red。",
            "6. battle_plan.resource_allocation 为对象数组：target/allocation_pct/reason。",
            "7. battle_plan.critical_tasks 为对象数组：task/focus/guardrail。",
            "",
            "请在保留当前证据事实的前提下，尽量强化判断与策略质量。",
            "",
            "证据与规则兜底如下：",
            json.dumps(fallback_briefing, ensure_ascii=False, indent=2),
        ]
    )


def _extract_json_block(text: str) -> Dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        raise AIPlannerError("模型未返回结构化内容")
    fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*\})\s*```", raw)
    if fenced:
        raw = fenced.group(1).strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"(\{[\s\S]*\})", raw)
        if not match:
            raise AIPlannerError("模型输出不是有效 JSON")
        parsed = json.loads(match.group(1))
    if not isinstance(parsed, dict):
        raise AIPlannerError("模型输出结构无效")
    return parsed


def _normalize_briefing_payload(candidate: Dict[str, Any], fallback_briefing: Dict[str, Any]) -> Dict[str, Any]:
    fallback_meta = fallback_briefing["meta"]
    fallback_diag = fallback_briefing["diagnosis"]
    fallback_plan = fallback_briefing["battle_plan"]
    fallback_evidence = fallback_briefing["evidence"]

    diagnosis = candidate.get("diagnosis") if isinstance(candidate.get("diagnosis"), dict) else {}
    battle_plan = candidate.get("battle_plan") if isinstance(candidate.get("battle_plan"), dict) else {}
    narrative = candidate.get("narrative") if isinstance(candidate.get("narrative"), dict) else {}

    merged = {
        "meta": {
            **fallback_meta,
            **(candidate.get("meta") or {}),
        },
        "diagnosis": {
            **fallback_diag,
            **diagnosis,
            "key_signals": (diagnosis.get("key_signals") or fallback_diag.get("key_signals") or [])[:5],
            "risks": (diagnosis.get("risks") or fallback_diag.get("risks") or [])[:4],
            "opportunities": (diagnosis.get("opportunities") or fallback_diag.get("opportunities") or [])[:3],
        },
        "battle_plan": {
            **fallback_plan,
            **battle_plan,
            "secondary_objectives": (battle_plan.get("secondary_objectives") or fallback_plan.get("secondary_objectives") or [])[:3],
            "resource_allocation": battle_plan.get("resource_allocation") or fallback_plan.get("resource_allocation") or [],
            "critical_tasks": battle_plan.get("critical_tasks") or fallback_plan.get("critical_tasks") or [],
            "execution_rhythm": (battle_plan.get("execution_rhythm") or fallback_plan.get("execution_rhythm") or [])[:4],
            "anti_patterns": (battle_plan.get("anti_patterns") or fallback_plan.get("anti_patterns") or [])[:4],
        },
        "evidence": fallback_evidence,
    }
    merged_narrative = _render_narrative_markdown(
        merged["meta"],
        merged["diagnosis"],
        merged["battle_plan"],
        merged["evidence"],
    )
    merged["narrative"] = {
        **merged_narrative,
        **narrative,
        "analysis_markdown": narrative.get("analysis_markdown") or merged_narrative["analysis_markdown"],
        "plan_markdown": narrative.get("plan_markdown") or merged_narrative["plan_markdown"],
        "full_markdown": narrative.get("full_markdown") or merged_narrative["full_markdown"],
    }
    status = str(merged["diagnosis"].get("status_level") or fallback_diag.get("status_level") or "yellow").lower()
    if status not in {"green", "yellow", "red"}:
        merged["diagnosis"]["status_level"] = fallback_diag.get("status_level", "yellow")
    return merged


def build_briefing_result(
    meta: Dict[str, Any],
    stats: Dict[str, Any],
    prev_stats: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    fallback_briefing = _briefing_fallback(meta, stats, prev_stats)
    prompt = _build_structured_briefing_prompt(fallback_briefing)
    try:
        model_text = llm_client._call_qwen(prompt)
        parsed = _extract_json_block(model_text)
        return _normalize_briefing_payload(parsed, fallback_briefing)
    except AIPlannerError:
        raise
    except Exception as exc:
        raise AIPlannerError(f"结构化简报生成失败：{exc}") from exc


__all__ = [
    "_build_evidence_payload",
    "_build_rule_based_diagnosis",
    "_build_rule_based_plan",
    "_render_narrative_markdown",
    "_briefing_fallback",
    "build_briefing_result",
]
