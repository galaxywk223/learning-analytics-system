from datetime import date, timedelta
from unittest.mock import patch

from app.models import LogEntry, Stage
from app.services.ai_planner.errors import AIPlannerError


def _seed_stage_data(db_session, user_id):
    stage = Stage(
        name="大三下冲刺",
        start_date=date.today() - timedelta(days=20),
        user_id=user_id,
    )
    db_session.session.add(stage)
    db_session.session.commit()

    for offset, duration, task in [
        (0, 180, "算法冲刺"),
        (1, 150, "算法冲刺"),
        (2, 90, "科研阅读"),
        (3, 210, "算法冲刺"),
    ]:
        db_session.session.add(
            LogEntry(
                log_date=date.today() - timedelta(days=offset),
                task=task,
                actual_duration=duration,
                legacy_category="算法" if "算法" in task else "科研",
                mood=4,
                stage_id=stage.id,
            )
        )
    db_session.session.commit()
    return stage


def test_ai_briefing_fallback_returns_structured_result(
    client, db_session, register_and_login, auth_headers
):
    token, user_id = register_and_login()
    stage = _seed_stage_data(db_session, user_id)

    with patch("app.services.ai_planner.llm_client._call_qwen") as mock_qwen:
        mock_qwen.side_effect = AIPlannerError("Simulated API Failure")
        resp = client.post(
            "/api/ai/briefing",
            json={"scope": "stage", "stage_id": stage.id},
            headers=auth_headers(token),
        )

    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["meta"]["period_label"]
    assert data["diagnosis"]["status_level"] in {"green", "yellow", "red"}
    assert data["diagnosis"]["core_judgement"]
    assert len(data["diagnosis"]["key_signals"]) >= 1
    assert data["battle_plan"]["main_objective"]
    assert len(data["battle_plan"]["resource_allocation"]) >= 1
    assert data["narrative"]["full_markdown"].startswith("## 分析总结")


def test_ai_briefing_history_contains_summary_fields(
    client, db_session, register_and_login, auth_headers
):
    token, user_id = register_and_login()
    stage = _seed_stage_data(db_session, user_id)

    with patch("app.services.ai_planner.llm_client._call_qwen") as mock_qwen:
        mock_qwen.side_effect = AIPlannerError("Simulated API Failure")
        create_resp = client.post(
            "/api/ai/briefing",
            json={"scope": "stage", "stage_id": stage.id},
            headers=auth_headers(token),
        )

    assert create_resp.status_code == 200

    history_resp = client.get(
        "/api/ai/history?type=briefing",
        headers=auth_headers(token),
    )
    assert history_resp.status_code == 200
    items = history_resp.get_json()["data"]
    assert len(items) == 1
    assert items[0]["workflow_type"] == "briefing"
    assert items[0]["core_judgement"]
    assert items[0]["status_level"] in {"green", "yellow", "red"}
    assert items[0]["period_label"]


def test_ai_analysis_and_plan_reuse_briefing_structure(
    client, db_session, register_and_login, auth_headers
):
    token, user_id = register_and_login()
    _seed_stage_data(db_session, user_id)

    with patch("app.services.ai_planner.llm_client._call_qwen") as mock_qwen:
        mock_qwen.side_effect = AIPlannerError("Simulated API Failure")
        analysis_resp = client.post(
            "/api/ai/analysis",
            json={"scope": "week", "date": date.today().isoformat()},
            headers=auth_headers(token),
        )
        plan_resp = client.post(
            "/api/ai/plan",
            json={"scope": "week", "date": date.today().isoformat()},
            headers=auth_headers(token),
        )

    assert analysis_resp.status_code == 200
    analysis_data = analysis_resp.get_json()["data"]
    assert "briefing" in analysis_data
    assert analysis_data["text"].startswith("## 分析总结")

    assert plan_resp.status_code == 200
    plan_data = plan_resp.get_json()["data"]
    assert "briefing" in plan_data
    assert plan_data["text"].startswith("## 规划建议")
