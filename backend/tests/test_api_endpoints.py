"""Backend endpoint tests (structured records, dashboard summary, countdown enhancements, settings).
Using backend/app package directly (scheme A)."""

from datetime import date, datetime, timedelta
import pytz
import pytest

from app import create_app, db
from app.models import (
    Stage,
    LogEntry,
    WeeklyData,
    DailyData,
    CountdownEvent,

    Milestone,
    Motto,
    Setting,
)

# ---------------- Fixtures ----------------


@pytest.fixture(scope="function")
def app():
    _app = create_app("testing")
    with _app.app_context():
        yield _app


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def db_session(app):
    db.create_all()
    yield db
    db.session.remove()
    db.drop_all()


# ---------------- Helpers ----------------


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def register_and_login(client, username="u1", email="u1@test.com"):
    r = client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": "pw123"},
    )
    assert r.status_code in (201, 409)
    r = client.post("/api/auth/login", json={"email": email, "password": "pw123"})
    data = r.get_json()
    assert data["success"]
    return data["access_token"], data["user"]["id"]


# ---------------- Dashboard Summary ----------------


def test_dashboard_summary_empty(client, db_session):
    token, user_id = register_and_login(client)
    stage = Stage(name="阶段A", start_date=date.today(), user_id=user_id)
    db_session.session.add(stage)
    db_session.session.commit()
    resp = client.get("/api/users/dashboard/summary", headers=auth_headers(token))
    assert resp.status_code == 200
    payload = resp.get_json()["data"]
    assert payload["today_duration_minutes"] == 0
    assert payload["next_countdown"] is None
    assert payload["pending_todos"] == 0
    assert payload["milestones_count"] == 0
    assert payload["daily_plan"] == {"completed": 0, "total": 0}


def test_dashboard_summary_with_data(client, db_session):
    token, user_id = register_and_login(client, username="u2", email="u2@test.com")
    stage = Stage(name="阶段B", start_date=date.today(), user_id=user_id)
    db_session.session.add(stage)
    for dur in [30, 90]:
        db_session.session.add(
            LogEntry(
                log_date=date.today(),
                task=f"task{dur}",
                actual_duration=dur,
                stage_id=stage.id,
            )
        )
    future_dt = datetime.utcnow().replace(tzinfo=pytz.utc) + timedelta(days=3)
    db_session.session.add(
        CountdownEvent(title="考试", target_datetime_utc=future_dt, user_id=user_id)
    )

    db_session.session.add(
        Milestone(title="里程碑1", event_date=date.today(), user_id=user_id)
    )
    db_session.session.add(Motto(content="坚持就是胜利", user_id=user_id))
    db_session.session.commit()
    resp = client.get("/api/users/dashboard/summary", headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["today_duration_minutes"] == 120
    assert data["next_countdown"] is not None
    assert data["pending_todos"] == 0
    assert data["milestones_count"] == 1
    assert data["random_motto"] is not None


# ---------------- Structured Records ----------------


def test_structured_records_basic(client, db_session):
    token, user_id = register_and_login(client, username="u3", email="u3@test.com")
    stage = Stage(
        name="阶段C", start_date=date.today() - timedelta(days=10), user_id=user_id
    )
    db_session.session.add(stage)
    target_dates = [date.today() - timedelta(days=d) for d in range(0, 9)]
    for d in target_dates:
        db_session.session.add(
            LogEntry(log_date=d, task=f"学习{d}", actual_duration=60, stage_id=stage.id)
        )
        db_session.session.add(
            DailyData(log_date=d, efficiency=80.0, stage_id=stage.id)
        )
    db_session.session.add(
        WeeklyData(
            year=target_dates[0].year, week_num=1, efficiency=75.0, stage_id=stage.id
        )
    )
    db_session.session.add(
        WeeklyData(
            year=target_dates[0].year, week_num=2, efficiency=82.0, stage_id=stage.id
        )
    )
    db_session.session.commit()
    resp = client.get(
        f"/api/records/structured?stage_id={stage.id}", headers=auth_headers(token)
    )
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["success"]
    assert payload["summary"]["total_records"] == len(target_dates)
    assert len(payload["weeks"]) >= 2
    assert "weekly_efficiency" in payload["weeks"][0]
    assert "efficiency" in payload["weeks"][0]["days"][0]


def test_structured_records_missing_stage_id(client, db_session):
    token, _ = register_and_login(client, username="u4", email="u4@test.com")
    resp = client.get("/api/records/structured", headers=auth_headers(token))
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False


def test_structured_records_stage_not_owned(client, db_session):
    # user A 创建 stage
    token_a, user_a = register_and_login(client, username="a", email="a@test.com")
    stage = Stage(name="阶段X", start_date=date.today(), user_id=user_a)
    db_session.session.add(stage)
    db_session.session.commit()
    # user B 请求该 stage
    token_b, _ = register_and_login(client, username="b", email="b@test.com")
    resp = client.get(
        f"/api/records/structured?stage_id={stage.id}", headers=auth_headers(token_b)
    )
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["success"] is False


# ---------------- Countdown Enhancements ----------------


def test_countdowns_enhanced_fields(client, db_session):
    token, user_id = register_and_login(client, username="u5", email="u5@test.com")
    future = datetime.utcnow().replace(tzinfo=pytz.utc) + timedelta(days=5)
    past = datetime.utcnow().replace(tzinfo=pytz.utc) - timedelta(days=2)
    db_session.session.add(
        CountdownEvent(title="未来事件", target_datetime_utc=future, user_id=user_id)
    )
    db_session.session.add(
        CountdownEvent(title="过去事件", target_datetime_utc=past, user_id=user_id)
    )
    db_session.session.commit()
    resp = client.get("/api/countdowns", headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.get_json()
    events = data.get("events") or data.get("countdowns") or []
    assert len(events) == 2
    future_ev = next(e for e in events if e["title"] == "未来事件")
    past_ev = next(e for e in events if e["title"] == "过去事件")
    assert future_ev["is_expired"] is False and future_ev["remaining_days"] > 0
    assert past_ev["is_expired"] is True
    assert "progress_percentage" in future_ev


# ---------------- Settings CRUD ----------------


def test_settings_crud(client, db_session):
    token, user_id = register_and_login(client, username="u7", email="u7@test.com")
    # 初始为空
    resp = client.get("/api/users/settings", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.get_json()["settings"] == {}
    # 更新设置
    payload = {"theme": "palette-green", "layout_sidebar_collapsed": True}
    resp = client.post("/api/users/settings", json=payload, headers=auth_headers(token))
    assert resp.status_code == 200
    # 再次获取
    resp = client.get("/api/users/settings", headers=auth_headers(token))
    settings = resp.get_json()["settings"]
    assert settings["theme"] == "palette-green"
    assert settings["layout_sidebar_collapsed"] == "True"  # 存储为字符串
    # 确认数据库记录
    assert Setting.query.filter_by(user_id=user_id, key="theme").first() is not None


# ---------------- Auth Refresh ----------------


def test_auth_refresh(client, db_session):
    # 注册并登录拿到 refresh token
    client.post(
        "/api/auth/register",
        json={"username": "rf", "email": "rf@test.com", "password": "pw123"},
    )
    login_resp = client.post(
        "/api/auth/login", json={"email": "rf@test.com", "password": "pw123"}
    )
    login_data = login_resp.get_json()
    refresh_token = login_data["refresh_token"]
    # 使用 refresh token 获取新 access
    resp = client.post(
        "/api/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True
