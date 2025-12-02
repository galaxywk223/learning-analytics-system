from datetime import date
from typing import Any, Dict, Optional

from app.models import CountdownEvent


def _build_countdown_context(
    user_id: int, start_date: Optional[date], end_date: Optional[date]
) -> Dict[str, Any]:
    """
    Fetch all countdown events (historical + upcoming) and compute their
    relative distance to the current analysis window.
    """
    events = (
        CountdownEvent.query.filter(CountdownEvent.user_id == user_id)
        .order_by(CountdownEvent.target_datetime_utc.asc())
        .all()
    )
    reference_date = end_date or date.today()
    timeline: list[dict[str, Any]] = []
    sprint_events: list[dict[str, Any]] = []
    recovery_events: list[dict[str, Any]] = []

    for event in events:
        if not event.target_datetime_utc:
            continue
        event_date = event.target_datetime_utc.date()
        days_to_start = (event_date - start_date).days if start_date else None
        days_to_end = (event_date - end_date).days if end_date else None
        days_from_reference = (event_date - reference_date).days

        entry = {
            "id": event.id,
            "title": event.title,
            "event_date": event_date.isoformat(),
            "days_to_period_start": days_to_start,
            "days_to_period_end": days_to_end,
            "days_from_reference": days_from_reference,
        }
        timeline.append(entry)

        if days_to_end is None:
            continue
        # 冲刺类：未来 0-14 天
        if 0 <= days_to_end <= 14:
            sprint_events.append({**entry, "label": "冲刺类（高度紧迫）"})
        # 回血类：过去 0-7 天
        if -7 <= days_to_end < 0:
            recovery_events.append({**entry, "label": "刚刚完成，处于调整期"})

    pressure_phase = "balanced"
    if any(0 <= e.get("days_to_period_end", 99) <= 7 for e in timeline):
        pressure_phase = "sprint"
    elif any(-3 <= e.get("days_to_period_end", -99) < 0 for e in timeline):
        pressure_phase = "cooldown"

    return {
        "reference_date": reference_date.isoformat(),
        "timeline": timeline,
        "sprint_events": sprint_events,
        "recovery_events": recovery_events,
        "pressure_phase": pressure_phase,
    }


__all__ = ["_build_countdown_context"]
