from __future__ import annotations

from typing import Any, Dict, Optional

from app.models import Stage


def _build_analysis_prompt(
    scope: str,
    stats: Dict,
    stage: Optional[Stage],
    period_label: str,
    prev_stats: Optional[Dict] = None,
) -> str:
    lines = [
        "你是一位有同理心的资深学习教练（并肩作战的学长/学姐），用口语化、对话式中文回应用户。",
        "禁止使用公文风、翻译腔或类似“经分析”“由此可见”的书面化表达，要像真人交流。",
        "请严格基于下述统计数据给出中文分析总结，必须以事实为依据：",
        "- 不得编造未提供的数字或类别，如数据不足需显式说明；",
        "- 以要点列表和小标题组织，重点突出可验证的发现；",
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
        baseline = stats.get("efficiency_baseline") or {}
        base_all = baseline.get("all_time_avg")
        base_recent = baseline.get("last_30d_avg")
        peak_recent = baseline.get("last_30d_peak")
        parts = [f"当前平均效率：{stats['average_efficiency']}"]
        if base_all is not None:
            parts.append(f"历史平均：{base_all}")
        if base_recent is not None:
            parts.append(f"近30天平均：{base_recent}")
        if peak_recent is not None:
            parts.append(f"近30天最高：{peak_recent}")
        lines.append("- " + (f"{parts[0]}（" + "，".join(parts[1:]) + "）" if len(parts) > 1 else parts[0]))
    if stats.get("average_mood") is not None:
        lines.append(f"- 平均心情评分：{stats['average_mood']}")

    # 活跃占比、连续打卡
    if stats.get("total_days"):
        active_ratio = stats.get("active_ratio")
        if active_ratio is not None:
            lines.append(
                f"- 活跃天数：{stats.get('active_days', 0)}/{stats['total_days']}（活跃占比 {active_ratio*100:.1f}%）"
            )
    if stats.get("streak_longest"):
        lines.append(
            f"- 连续打卡：当前 {stats.get('streak_current', 0)} 天，历史最长 {stats['streak_longest']} 天"
        )

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

    # 时间分布偏好
    try:
        wd_sorted = sorted(stats.get("weekday_stats", []), key=lambda x: x.get("minutes", 0), reverse=True)
        top_wd = [w for w in wd_sorted[:2] if w.get("minutes", 0) > 0]
        if top_wd:
            wd_map = {0: "周一", 1: "周二", 2: "周三", 3: "周四", 4: "周五", 5: "周六", 6: "周日"}
            lines.append(
                "- 偏好日：" + "；".join([f"{wd_map.get(w['weekday'], w['weekday'])}（{w['hours']}h）" for w in top_wd])
            )
    except Exception:
        pass
    try:
        hr_sorted = sorted(stats.get("hour_stats", []), key=lambda x: x.get("minutes", 0), reverse=True)
        top_hr = [h for h in hr_sorted[:3] if h.get("minutes", 0) > 0]
        if top_hr:
            lines.append(
                "- 高效时段：" + "；".join([f"{h['hour']:02d}:00（{h['hours']}h）" for h in top_hr])
            )
    except Exception:
        pass

    # 与上一周期对比
    if prev_stats and prev_stats.get("total_minutes") is not None:
        cur_h = float(stats.get("total_hours", 0) or 0)
        prev_h = float(prev_stats.get("total_hours", 0) or 0)
        diff_h = cur_h - prev_h
        pct = (diff_h / prev_h * 100) if prev_h > 0 else None
        diff_str = (f"{diff_h:+.1f}h" + (f"（{pct:+.1f}%）" if pct is not None else ""))
        lines.append(f"- 与上一周期对比：总时长 {diff_str}")

    if stats["idle_days"]:
        lines.append(
            "- 以下日期未记录学习，可结合计划指出原因或提醒："
            + ", ".join(stats["idle_days"])
        )

    countdown_ctx = stats.get("countdown_context") or {}
    countdown_lines: list[str] = []
    ref_label = countdown_ctx.get("reference_date")

    def _render_event(entry: Dict[str, Any]) -> str:
        delta = entry.get("days_from_reference")
        if delta is None:
            return f"{entry.get('title')}（日期：{entry.get('event_date')}）"
        if delta > 0:
            return f"{entry.get('title')}（{delta} 天后，日期：{entry.get('event_date')}）"
        if delta == 0:
            return f"{entry.get('title')}（今天，日期：{entry.get('event_date')}）"
        return f"{entry.get('title')}（已过去 {abs(delta)} 天，日期：{entry.get('event_date')}）"

    sprint_events = countdown_ctx.get("sprint_events") or []
    if sprint_events:
        countdown_lines.append("  • 冲刺类（未来 0-14 天，高度紧迫）：")
        countdown_lines.extend([f"    - {_render_event(e)}" for e in sprint_events[:5]])

    recovery_events = countdown_ctx.get("recovery_events") or []
    if recovery_events:
        countdown_lines.append("  • 回血类（过去 0-7 天，调整期）：")
        countdown_lines.extend([f"    - {_render_event(e)}" for e in recovery_events[:5]])

    if countdown_ctx.get("timeline") and not countdown_lines:
        countdown_lines.append("  • 当前周期内暂无冲刺/回血类倒计时，但保留历史记录供参考。")

    if countdown_lines:
        prefix = f"- 时间节点与压力背景（参考日：{ref_label}）：\n" if ref_label else "- 时间节点与压力背景：\n"
        lines.append(prefix + "\n".join(countdown_lines))

    sprint_flag = bool(sprint_events)
    pressure_phase = countdown_ctx.get("pressure_phase", "balanced")
    phase_label = {
        "balanced": "平时模式：建议学/练/项目保持结构平衡。",
        "sprint": "冲刺模式：未来 7 天内有紧迫事件，允许单一目标击穿（偏科视为战术聚焦，应予以肯定）。",
        "cooldown": "回血模式：关键事件刚结束（3 天内），允许低效和休息，先恢复状态。",
    }.get(pressure_phase, "平时模式：建议学/练/项目保持结构平衡。")
    lines.append(
        "- 动态评价基准：平时追求结构平衡；倒计时 < 7 天时优先单点突破；倒计时结束 < 3 天时允许低效休整。"
    )
    lines.append(f"- 当前判定：{phase_label}")
    if sprint_flag:
        lines.append("- 提示：存在冲刺类事件，若出现单科专攻/偏科，请视为合理战术而非问题。")

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
    next_days: Optional[int] = None,
) -> str:
    lines = [
        "你是一位有同理心的资深学习教练（并肩作战的学长/学姐），用口语化、对话式中文给出行动建议。",
        "禁止使用公文风、翻译腔或类似“经分析”“由此可见”的书面化表达，要暖心、直接、可执行。",
        "请严格基于下述统计数据制定下一阶段的中文学习计划：",
        "- 只引用已提供的数据，不得臆测；",
        "- 结果需结构清晰（小标题+要点），包含可执行清单；",
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
        baseline = stats.get("efficiency_baseline") or {}
        base_all = baseline.get("all_time_avg")
        base_recent = baseline.get("last_30d_avg")
        peak_recent = baseline.get("last_30d_peak")
        parts = [f"当前平均效率：{stats['average_efficiency']}"]
        if base_all is not None:
            parts.append(f"历史平均：{base_all}")
        if base_recent is not None:
            parts.append(f"近30天平均：{base_recent}")
        if peak_recent is not None:
            parts.append(f"近30天最高：{peak_recent}")
        lines.append("- " + (f"{parts[0]}（" + "，".join(parts[1:]) + "）" if len(parts) > 1 else parts[0]))

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

    if next_days:
        lines.append(f"- 下一阶段天数：约 {next_days} 天（用于时间预算与节奏安排参考）")

    countdown_ctx = stats.get("countdown_context") or {}
    countdown_lines: list[str] = []
    ref_label = countdown_ctx.get("reference_date")

    def _render_event(entry: Dict[str, Any]) -> str:
        delta = entry.get("days_from_reference")
        if delta is None:
            return f"{entry.get('title')}（日期：{entry.get('event_date')}）"
        if delta > 0:
            return f"{entry.get('title')}（{delta} 天后，日期：{entry.get('event_date')}）"
        if delta == 0:
            return f"{entry.get('title')}（今天，日期：{entry.get('event_date')}）"
        return f"{entry.get('title')}（已过去 {abs(delta)} 天，日期：{entry.get('event_date')}）"

    sprint_events = countdown_ctx.get("sprint_events") or []
    recovery_events = countdown_ctx.get("recovery_events") or []
    if sprint_events:
        countdown_lines.append("  • 冲刺类：未来 0-14 天内的高优先事件")
        countdown_lines.extend([f"    - {_render_event(e)}" for e in sprint_events[:5]])
    if recovery_events:
        countdown_lines.append("  • 回血类：过去 0-7 天的事件，需预留恢复/总结")
        countdown_lines.extend([f"    - {_render_event(e)}" for e in recovery_events[:5]])
    if countdown_lines:
        prefix = f"- 时间节点与压力背景（参考日：{ref_label}）：\n" if ref_label else "- 时间节点与压力背景：\n"
        lines.append(prefix + "\n".join(countdown_lines))

    pressure_phase = countdown_ctx.get("pressure_phase", "balanced")
    phase_label = {
        "balanced": "平时模式：保持学/练/项目均衡。",
        "sprint": "冲刺模式：未来 7 天内有关键节点，允许单一目标击穿与偏科。",
        "cooldown": "回血模式：关键节点刚结束（3 天内），优先恢复和总结。",
    }.get(pressure_phase, "平时模式：保持学/练/项目均衡。")
    lines.append(
        "- 动态节奏原则：平时保持平衡；倒计时 < 7 天时聚焦单点突破；事件结束 < 3 天时安排休整与反思。"
    )
    lines.append(f"- 当前判定：{phase_label}")
    if sprint_events:
        lines.append("- 若存在冲刺类事件，请将偏科/单科深挖视为合理战术，并在计划中给予肯定与保护时间。")

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


def _fallback_analysis_text(scope: str, stats: Dict, period_label: str, prev_stats: Optional[Dict]) -> str:
    lines: list[str] = []
    lines.append(f"## 分析总结 · {period_label}")
    lines.append("")
    lines.append("### 数据概览")
    lines.append(
        f"- 总时长：{stats.get('total_hours', 0)}h（{stats.get('total_minutes', 0)} 分钟） | 记录：{stats.get('total_sessions', 0)} 条"
    )
    if stats.get("average_daily_minutes"):
        lines.append(f"- 平均每日：{stats['average_daily_minutes']} 分钟")
    if stats.get("average_efficiency") is not None:
        lines.append(f"- 平均效率：{stats['average_efficiency']}")
    if stats.get("average_mood") is not None:
        lines.append(f"- 平均心情：{stats['average_mood']}")
    if stats.get("active_ratio") is not None and stats.get("total_days"):
        lines.append(
            f"- 活跃天数：{stats.get('active_days', 0)}/{stats['total_days']}（{round(stats['active_ratio']*100,1)}%） | 连击：当前 {stats.get('streak_current',0)} 天 / 最长 {stats.get('streak_longest',0)} 天"
        )

    lines.append("")
    if stats.get("category_stats"):
        lines.append("### 主要投入方向（Top 5）")
        for item in stats["category_stats"][:5]:
            lines.append(f"- {item['name']}：{item['hours']}h（{item['percentage']}%）")

    if stats.get("top_tasks"):
        lines.append("")
        lines.append("### 高频任务")
        for item in stats["top_tasks"]:
            lines.append(f"- {item['task']}：{item['hours']}h（{item['percentage']}%）")

    # 时间偏好
    top_hours = sorted(stats.get("hour_stats", []), key=lambda x: x.get("minutes", 0), reverse=True)[:3]
    if any(h.get("minutes", 0) for h in top_hours):
        lines.append("")
        lines.append("### 高效时段")
        lines.append("、".join([f"{h['hour']:02d}:00（{h['hours']}h）" for h in top_hours if h.get('minutes',0)>0]))

    # 对比
    if prev_stats and prev_stats.get("total_hours") is not None:
        cur = float(stats.get("total_hours", 0) or 0)
        prev = float(prev_stats.get("total_hours", 0) or 0)
        diff = cur - prev
        pct = (diff / prev * 100) if prev > 0 else None
        lines.append("")
        lines.append("### 与上一周期对比")
        lines.append(f"- 总时长：{diff:+.1f}h" + (f"（{pct:+.1f}%）" if pct is not None else ""))

    if stats.get("idle_days"):
        lines.append("")
        lines.append("### 提醒")
        lines.append("- 有未记录的日期：" + ", ".join(stats["idle_days"]))

    lines.append("")
    lines.append(
        "> 本段为离线模板生成（模型连接异常时的兜底结果），仅依据统计数据输出。"
    )
    return "\n".join(lines)


def _fallback_plan_text(scope: str, stats: Dict, period_label: str, next_period_label: str, next_days: Optional[int]) -> str:
    avg_daily = float(stats.get("average_daily_minutes", 0) or 0)
    baseline_daily_h = round(avg_daily / 60, 1) if avg_daily else 1.5
    total_budget_h = round((next_days or 7) * baseline_daily_h, 1)
    lines: list[str] = []
    lines.append(f"## 规划建议 · {next_period_label}")
    lines.append("")
    lines.append("### 目标与节奏")
    lines.append(f"- 总投入预算：≈ {total_budget_h} 小时（按 {baseline_daily_h}h/日 × {next_days or 7} 天估算）")
    lines.append("- 节奏：优先安排 3–4 个重点主题，每日至少 1 次复盘记录")

    # 类别分配（按历史占比微调）
    cats = stats.get("category_stats", [])[:4]
    if cats:
        lines.append("")
        lines.append("### 建议分配（按历史占比参考）")
        for c in cats:
            share = float(c.get("percentage", 0) or 0) / 100.0
            alloc = round(total_budget_h * share, 1)
            lines.append(f"- {c['name']}：约 {alloc}h（历史占比 {c['percentage']}%）")

    if stats.get("top_tasks"):
        lines.append("")
        lines.append("### 重点任务候选（来自历史高频）")
        for t in stats["top_tasks"]:
            lines.append(f"- {t['task']}：建议投入 {max(0.5, round(t['hours']*0.3,1))}h")

    lines.append("")
    lines.append("### 习惯与效率")
    lines.append("- 固定番茄时段：选择你的高效时段开展重难点学习")
    if stats.get("streak_current") is not None:
        lines.append(f"- 连击目标：在当前 {stats.get('streak_current',0)} 天基础上，争取 +3 天")
    lines.append("- 每日复盘：记录 1 句反思或心得，保留数据闭环")

    lines.append("")
    lines.append(
        "> 本段为离线模板生成（模型连接异常时的兜底结果），仅依据统计数据输出。"
    )
    return "\n".join(lines)


__all__ = [
    "_build_analysis_prompt",
    "_build_plan_prompt",
    "_fallback_analysis_text",
    "_fallback_plan_text",
]
