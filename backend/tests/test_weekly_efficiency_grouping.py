from datetime import date
import math

from app.models import User, Stage, LogEntry, DailyData, WeeklyData
from app.services.chart_service import get_chart_data_for_user
from app.services.helpers import get_custom_week_info
from app.services.record_service import recalculate_efficiency_for_stage


def _create_user():
    user = User(username="week-user", email="week-user@test.com")
    user.set_password("pw123")
    return user


def test_custom_week_info_uses_monday_boundary_after_partial_first_week():
    start_date = date(2026, 3, 5)  # Thursday

    assert get_custom_week_info(date(2026, 3, 5), start_date) == (2026, 1)
    assert get_custom_week_info(date(2026, 3, 8), start_date) == (2026, 1)
    assert get_custom_week_info(date(2026, 3, 9), start_date) == (2026, 2)
    assert get_custom_week_info(date(2026, 3, 15), start_date) == (2026, 2)
    assert get_custom_week_info(date(2026, 3, 16), start_date) == (2026, 3)


def test_recalculate_efficiency_splits_partial_first_week(db_session):
    user = _create_user()
    db_session.session.add(user)
    db_session.session.flush()

    stage = Stage(name="阶段A", start_date=date(2026, 3, 5), user_id=user.id)
    db_session.session.add(stage)
    db_session.session.flush()

    db_session.session.add_all(
        [
            LogEntry(
                log_date=date(2026, 3, 7),
                task="week1",
                actual_duration=120,
                mood=4,
                stage_id=stage.id,
            ),
            LogEntry(
                log_date=date(2026, 3, 10),
                task="week2",
                actual_duration=120,
                mood=4,
                stage_id=stage.id,
            ),
        ]
    )
    db_session.session.commit()

    recalculate_efficiency_for_stage(stage)

    weekly_rows = (
        WeeklyData.query.filter_by(stage_id=stage.id)
        .order_by(WeeklyData.week_num.asc())
        .all()
    )

    assert [row.week_num for row in weekly_rows] == [1, 2]
    assert all(row.efficiency is not None and row.efficiency > 0 for row in weekly_rows)


def test_weekly_efficiency_chart_aggregates_from_daily_data(db_session):
    user = _create_user()
    db_session.session.add(user)
    db_session.session.flush()

    stage = Stage(name="阶段B", start_date=date(2026, 3, 2), user_id=user.id)
    db_session.session.add(stage)
    db_session.session.flush()

    db_session.session.add_all(
        [
            LogEntry(
                log_date=date(2026, 3, 2),
                task="day1",
                actual_duration=120,
                mood=4,
                stage_id=stage.id,
            ),
            LogEntry(
                log_date=date(2026, 3, 3),
                task="day2",
                actual_duration=60,
                mood=5,
                stage_id=stage.id,
            ),
            DailyData(log_date=date(2026, 3, 2), efficiency=3.0, stage_id=stage.id),
            DailyData(log_date=date(2026, 3, 3), efficiency=5.0, stage_id=stage.id),
        ]
    )
    db_session.session.commit()

    payload = get_chart_data_for_user(user.id)

    assert payload["weekly_efficiency_data"]["labels"] == ["2026-W01"]
    assert payload["weekly_efficiency_data"]["actuals"] == [4.0]
    assert math.isclose(
        payload["daily_efficiency_data"]["actuals"][0], 3.0, rel_tol=1e-9
    )
