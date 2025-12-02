from datetime import date, timedelta
from typing import Dict, Optional

from app.models import DailyData, Stage


def _compute_efficiency_baseline(
    user_id: int, reference_date: Optional[date]
) -> Dict[str, Optional[float]]:
    """
    Compute historical efficiency baselines for context:
    - all-time average
    - last 30 days average
    - last 30 days peak
    """
    ref = reference_date or date.today()
    base_query = (
        DailyData.query.join(Stage, DailyData.stage_id == Stage.id)
        .filter(Stage.user_id == user_id)
    )

    all_rows = base_query.all()
    all_values = [r.efficiency for r in all_rows if r.efficiency is not None]

    last_30_start = ref - timedelta(days=29)
    recent_rows = base_query.filter(
        DailyData.log_date >= last_30_start, DailyData.log_date <= ref
    ).all()
    recent_values = [r.efficiency for r in recent_rows if r.efficiency is not None]

    def _avg(values: list[float]) -> Optional[float]:
        return round(sum(values) / len(values), 2) if values else None

    return {
        "all_time_avg": _avg(all_values),
        "last_30d_avg": _avg(recent_values),
        "last_30d_peak": round(max(recent_values), 2) if recent_values else None,
    }


__all__ = ["_compute_efficiency_baseline"]
