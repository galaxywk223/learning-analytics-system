from datetime import date, timedelta
from unittest.mock import patch

from app.models import AIChatMessage, AIChatSession, LogEntry, Stage
from app.services.ai_planner.errors import AIPlannerError


def _seed_chat_data(db_session, user_id):
    stage = Stage(
        name="大三下冲刺",
        start_date=date.today() - timedelta(days=40),
        user_id=user_id,
    )
    db_session.session.add(stage)
    db_session.session.commit()

    rows = [
        (0, 120, "算法-CCF CSP 刷题", "算法"),
        (1, 110, "科研-论文阅读", "科研"),
        (2, 80, "英语-听力", "英语"),
        (3, 150, "算法-限时模拟", "算法"),
        (5, 90, "科研-复现", "科研"),
    ]
    for offset, duration, task, category in rows:
        db_session.session.add(
            LogEntry(
                log_date=date.today() - timedelta(days=offset),
                task=task,
                actual_duration=duration,
                legacy_category=category,
                mood=4,
                stage_id=stage.id,
            )
        )
    db_session.session.commit()
    return stage


def test_chat_message_creates_session_and_visible_messages(
    client, db_session, register_and_login, auth_headers
):
    token, user_id = register_and_login()
    stage = _seed_chat_data(db_session, user_id)

    with patch("app.services.ai_planner.chat._call_qwen") as mock_qwen:
        mock_qwen.side_effect = [
            '{"decision":"need_more_context","needed_modules":["task_focus_detail"],"focus":"追问任务","answer_strategy":"先回答，再给任务建议"}',
            "你现在最该做的不是继续摊大饼，而是把算法冲刺和科研主线拆成可交付结果。",
        ]
        response = client.post(
            "/api/ai/chat/messages",
            json={
                "scope": "stage",
                "stage_id": stage.id,
                "content": "我下周该怎么安排？",
            },
            headers=auth_headers(token),
        )

    assert response.status_code == 200
    payload = response.get_json()["data"]
    assert payload["session"]["id"]
    assert payload["user_message"]["role"] == "user"
    assert payload["assistant_message"]["role"] == "assistant"
    assert payload["meta"]["used_modules"] == ["task_focus_detail"]
    assert AIChatSession.query.count() == 1
    assert AIChatMessage.query.count() == 2
    assert payload["session"]["scope"] == "stage"


def test_chat_message_ignores_unknown_modules(
    client, db_session, register_and_login, auth_headers
):
    token, user_id = register_and_login(username="u2", email="u2@test.com")
    _seed_chat_data(db_session, user_id)

    with patch("app.services.ai_planner.chat._call_qwen") as mock_qwen:
        mock_qwen.side_effect = [
            '{"decision":"need_more_context","needed_modules":["unknown_module","forecast_detail"],"focus":"预测","answer_strategy":"直接回答"}',
            "如果你关心下周走势，先看预测，再决定是否加码。",
        ]
        response = client.post(
            "/api/ai/chat/messages",
            json={
                "scope": "week",
                "date": date.today().isoformat(),
                "content": "下周趋势怎么看？",
            },
            headers=auth_headers(token),
        )

    assert response.status_code == 200
    payload = response.get_json()["data"]
    assert payload["meta"]["used_modules"] == ["forecast_detail"]


def test_chat_message_defaults_to_global_scope_when_scope_missing(
    client, db_session, register_and_login, auth_headers
):
    token, user_id = register_and_login(username="u5", email="u5@test.com")
    _seed_chat_data(db_session, user_id)

    with patch("app.services.ai_planner.chat._call_qwen") as mock_qwen:
        mock_qwen.side_effect = [
            '{"decision":"need_more_context","needed_modules":["trend_daily_detail"],"time_windows":["current_week"],"focus":"看近一周","answer_strategy":"先看近一周再回答"}',
            "你最近一周的波动比总览更明显，重点问题出在节奏断档。",
        ]
        response = client.post(
            "/api/ai/chat/messages",
            json={"content": "我最近到底哪里有问题？"},
            headers=auth_headers(token),
        )

    assert response.status_code == 200
    payload = response.get_json()["data"]
    assert payload["session"]["scope"] == "global"
    assert payload["meta"]["used_modules"] == ["trend_daily_detail"]


def test_chat_message_falls_back_to_conversational_reply(
    client, db_session, register_and_login, auth_headers
):
    token, user_id = register_and_login(username="u3", email="u3@test.com")
    _seed_chat_data(db_session, user_id)

    with patch("app.services.ai_planner.chat._call_qwen") as mock_qwen:
        mock_qwen.side_effect = AIPlannerError("model unavailable")
        response = client.post(
            "/api/ai/chat/messages",
            json={
                "scope": "week",
                "date": date.today().isoformat(),
                "content": "我这周最大的问题是什么？",
            },
            headers=auth_headers(token),
        )

    assert response.status_code == 200
    payload = response.get_json()["data"]
    assert payload["assistant_message"]["generation_mode"] == "rule_fallback"
    assert "我先直接回答你这个问题" in payload["assistant_message"]["content"]


def test_chat_session_history_only_contains_visible_messages(
    client, db_session, register_and_login, auth_headers
):
    token, user_id = register_and_login(username="u4", email="u4@test.com")
    _seed_chat_data(db_session, user_id)

    captured_prompts: list[str] = []

    def _fake_qwen(prompt: str):
        captured_prompts.append(prompt)
        if len(captured_prompts) % 2 == 1:
            return '{"decision":"answer_with_current_context","needed_modules":[],"focus":"连续对话","answer_strategy":"结合上下文继续回答"}'
        return "继续往下看，你的主线其实已经很清楚。"

    with patch("app.services.ai_planner.chat._call_qwen", side_effect=_fake_qwen):
        first = client.post(
            "/api/ai/chat/messages",
            json={
                "scope": "week",
                "date": date.today().isoformat(),
                "content": "先帮我看这周的状态。",
            },
            headers=auth_headers(token),
        )
        session_id = first.get_json()["data"]["session"]["id"]
        second = client.post(
            "/api/ai/chat/messages",
            json={
                "session_id": session_id,
                "scope": "week",
                "date": date.today().isoformat(),
                "content": "那我下周该砍掉什么？",
            },
            headers=auth_headers(token),
        )

    assert second.status_code == 200
    assert "先帮我看这周的状态" in captured_prompts[2]

    sessions_resp = client.get("/api/ai/chat/sessions", headers=auth_headers(token))
    assert sessions_resp.status_code == 200
    sessions = sessions_resp.get_json()["data"]
    assert len(sessions) == 1

    messages_resp = client.get(
        f"/api/ai/chat/sessions/{session_id}/messages",
        headers=auth_headers(token),
    )
    assert messages_resp.status_code == 200
    messages = messages_resp.get_json()["data"]["messages"]
    assert len(messages) == 4
    assert all(message["role"] in {"user", "assistant"} for message in messages)
