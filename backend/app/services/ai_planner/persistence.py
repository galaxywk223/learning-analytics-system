from datetime import date
from typing import Dict, Optional

from app import db
from app.models import AIInsight


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


__all__ = ["_save_insight"]
