"""
AI planning and analysis service using Qwen (DashScope OpenAI-compatible API).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from flask import current_app
import time

try:
    from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError
except ImportError:  # pragma: no cover - handled at runtime
    OpenAI = None  # type: ignore[assignment]
    APIConnectionError = APIStatusError = RateLimitError = Exception  # type: ignore[assignment]

from app import db
from app.models import AIInsight, DailyData, LogEntry, Stage, SubCategory


SCOPE_LABELS = {
    "day": "日度",
    "week": "周度",
    "month": "月度",
    "stage": "阶段",
}

# Cache a single client per API key/base_url to avoid re-instantiating the SDK on every call.
_qwen_client_cache: Dict[str, Any] = {}


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


def _get_prev_range(
    scope: str,
    start: Optional[date],
    end: Optional[date],
) -> Tuple[Optional[date], Optional[date]]:
    """Return the previous window relative to [start, end] for day/week/month.
    Stage 级别不提供上一阶段（因无法可靠推断）。
    """
    scope = scope.lower()
    if not start or not end:
        return None, None
    if scope == "day":
        prev = start - timedelta(days=1)
        return prev, prev
    if scope == "week":
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=6)
        return prev_start, prev_end
    if scope == "month":
        prev_end = start - timedelta(days=1)
        prev_start = prev_end.replace(day=1)
        return prev_start, prev_end
    return None, None



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
    weekday_minutes: Dict[int, int] = defaultdict(int)  # 0=Mon ... 6=Sun
    hour_minutes: Dict[int, int] = defaultdict(int)  # 0-23
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
        try:
            # 「活跃时段」统计：使用开始时间 hour，如果缺失则跳过
            if getattr(log, "start_time", None):
                hour = int(str(log.start_time)[0:2])  # 支持 "HH:MM:SS" 或 datetime
                if 0 <= hour <= 23:
                    hour_minutes[hour] += minutes
        except Exception:
            pass
        try:
            weekday = log_day.weekday()
            weekday_minutes[weekday] += minutes
        except Exception:
            pass

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

    # 活跃占比与学习打卡连击（当前/最长连续）
    total_days = None
    active_ratio = None
    current_streak = 0
    longest_streak = 0
    if start_date and end_date:
        total_days = (end_date - start_date).days + 1
        if total_days > 0:
            active_ratio = round(active_days / total_days, 3)
        # 计算 streak
        run = 0
        current = start_date
        last_day_with_log = None
        while current <= end_date:
            if current in daily_minutes and daily_minutes[current] > 0:
                run += 1
                longest_streak = max(longest_streak, run)
                last_day_with_log = current
            else:
                run = 0
            current += timedelta(days=1)
        # 计算当前连击：从区间末尾往前
        run = 0
        current = end_date
        while current >= start_date:
            if current in daily_minutes and daily_minutes[current] > 0:
                run += 1
                current -= timedelta(days=1)
            else:
                break
        current_streak = run

    # 将 weekday/hour 统计转为列表并补齐缺失键
    weekday_stats = [
        {
            "weekday": i,  # 0=Mon
            "minutes": int(weekday_minutes.get(i, 0)),
            "hours": round(weekday_minutes.get(i, 0) / 60, 2),
        }
        for i in range(7)
    ]
    hour_stats = [
        {
            "hour": h,
            "minutes": int(hour_minutes.get(h, 0)),
            "hours": round(hour_minutes.get(h, 0) / 60, 2),
        }
        for h in range(24)
    ]

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
        'total_days': total_days,
        'active_days': active_days,
        'active_ratio': active_ratio,
        'streak_current': current_streak,
        'streak_longest': longest_streak,
        'weekday_stats': weekday_stats,
        'hour_stats': hour_stats,
    }




def _configure_qwen():
    if OpenAI is None:
        raise AIPlannerError(
            "未安装 openai SDK，请先 pip install openai 或运行 pip install -r requirements.txt 安装依赖"
        )
    api_key = current_app.config.get("QWEN_API_KEY")
    if not api_key:
        raise AIPlannerError("未配置 Qwen API 密钥")
    base_url = current_app.config.get(
        "QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    cache_key = f"{api_key}@{base_url}"
    client = _qwen_client_cache.get(cache_key)
    if client is None:
        client = OpenAI(api_key=api_key, base_url=base_url)
        _qwen_client_cache.clear()
        _qwen_client_cache[cache_key] = client
    model_name = current_app.config.get("QWEN_MODEL", "qwen-plus-2025-07-28")
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
    prev_stats: Optional[Dict] = None,
) -> str:
    lines = [
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
        lines.append(f"- 平均效率：{stats['average_efficiency']}")
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

    if next_days:
        lines.append(f"- 下一阶段天数：约 {next_days} 天（用于时间预算与节奏安排参考）")

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


def _call_qwen(prompt: str) -> str:
    client, model_name = _configure_qwen()
    max_retries = int(current_app.config.get("AI_MAX_RETRIES", 2) or 0)
    backoff = float(current_app.config.get("AI_RETRY_BACKOFF", 1.25) or 1.25)
    attempt = 0
    last_error: Exception | None = None
    while attempt <= max_retries:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            if not response or not getattr(response, "choices", None):
                raise AIPlannerError("未能生成有效的模型输出")
            message = response.choices[0].message.content if response.choices else None
            if not message:
                raise AIPlannerError("模型未返回内容，请稍后重试")
            return str(message).strip()
        except (APIStatusError, RateLimitError) as exc:
            last_error = exc
            detail = getattr(exc, "message", None) or getattr(exc, "response", None) or str(exc)
            # 对临时性错误做重试
            transient = any(
                key in str(detail).lower()
                for key in [
                    "timeout",
                    "temporarily",
                    "unavailable",
                    "deadline",
                    "internal",
                    "quota",
                    "network",
                    "503",
                ]
            )
            if attempt < max_retries and transient:
                time.sleep(max(0.2, 0.6 * (backoff ** attempt)))
                attempt += 1
                continue
            raise AIPlannerError(
                f"调用通义千问接口失败：{detail}（模型：{model_name}）"
            ) from exc
        except APIConnectionError as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(max(0.2, 0.6 * (backoff ** attempt)))
                attempt += 1
                continue
            raise AIPlannerError("连接通义千问失败，请检查网络后重试") from exc
        except Exception as exc:
            last_error = exc
            # 常见 SSL/连接错误
            msg = str(exc)
            if attempt < max_retries and any(
                s in msg for s in [
                    "SSL:",
                    "EOF occurred",
                    "Connection reset",
                    "Connection aborted",
                    "RemoteDisconnected",
                ]
            ):
                time.sleep(max(0.2, 0.6 * (backoff ** attempt)))
                attempt += 1
                continue
            raise AIPlannerError(f"生成内容失败，请稍后重试：{exc}") from exc

    # 理论上到不了这里
    if last_error:
        raise AIPlannerError(f"生成内容失败，请稍后重试：{last_error}")
    raise AIPlannerError("生成内容失败：未知原因")


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
    # 上一周期（仅限日/周/月）
    prev_start, prev_end = _get_prev_range(scope, start, end)
    prev_stats = None
    if prev_start and prev_end and scope != "stage":
        prev_stats = _aggregate_learning_data(user_id, prev_start, prev_end, None)
    period_label = _format_period_label(scope, start, end)
    prompt = _build_analysis_prompt(scope, stats, stage, period_label, prev_stats)
    try:
        output_text = _call_qwen(prompt)
    except AIPlannerError as exc:
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
    except AIPlannerError as exc:
        if current_app.config.get("AI_ENABLE_FALLBACK", True):
            output_text = _fallback_plan_text(scope, stats, period_label, next_period_label or "后续阶段", next_days)
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

