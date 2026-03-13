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
    assert data["meta"]["generation_mode"] == "rule_fallback"
    assert data["meta"]["generation_label"] == "规则兜底"
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
    assert items[0]["generation_mode"] == "rule_fallback"
    assert items[0]["generation_label"] == "规则兜底"


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


def test_ai_briefing_marks_llm_enhanced_when_model_succeeds(
    client, db_session, register_and_login, auth_headers
):
    token, user_id = register_and_login()
    stage = _seed_stage_data(db_session, user_id)

    with patch("app.services.ai_planner.llm_client._call_qwen") as mock_qwen:
        mock_qwen.return_value = """
        {
          "diagnosis": {
            "core_judgement": "当前不是失控，而是主轴推进不够狠，必须更明确地集中火力。",
            "status_level": "yellow",
            "key_signals": ["科研和算法是当前最真实的两条主轴，不该再被边缘任务分散注意力。"],
            "risks": ["如果继续平均用力，下一周期大概率还会维持表面忙碌、主线推进不足。"],
            "opportunities": ["算法冲刺已经有连续投入痕迹，可以直接放大成明确的结果导向任务。"],
            "strategy_bias": "继续保留双主轴，但把更多高质量时段明确让给最关键任务。"
          },
          "battle_plan": {
            "main_objective": "下一周期把算法冲刺和科研主线都推进到能看见结果的层级。",
            "secondary_objectives": ["减少边缘任务挤占主时段。"],
            "resource_allocation": [
              {"target": "算法", "allocation_pct": 55, "reason": "结果最容易在短周期内兑现"},
              {"target": "科研", "allocation_pct": 35, "reason": "保持主线推进"},
              {"target": "整理复盘", "allocation_pct": 10, "reason": "只保留必要纠偏"}
            ],
            "critical_tasks": [
              {"task": "算法冲刺", "focus": "直接推进最难题型，不再停留在熟练区。", "guardrail": "每次结束都要留下结果记录。"}
            ],
            "execution_rhythm": ["先打穿算法，再补科研。"],
            "anti_patterns": ["不要把时间消耗在伪整理上。"],
            "next_review_point": "执行 3 天后做第一次偏差检查"
          }
        }
        """
        resp = client.post(
            "/api/ai/briefing",
            json={"scope": "stage", "stage_id": stage.id},
            headers=auth_headers(token),
        )

    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["meta"]["generation_mode"] == "llm_enhanced"
    assert data["meta"]["generation_label"] == "LLM增强"


def test_ai_briefing_rewrites_when_llm_output_too_close_to_fallback(
    client, db_session, register_and_login, auth_headers
):
    token, user_id = register_and_login()
    stage = _seed_stage_data(db_session, user_id)

    with patch("app.services.ai_planner.llm_client._call_qwen") as mock_qwen:
        mock_qwen.side_effect = [
            """
            {
              "diagnosis": {
                "core_judgement": "现在最大的问题不是不努力，而是策略失焦和效率泄漏。",
                "status_level": "red",
                "key_signals": ["阶段（2026-02-21 至 2026-03-13） 内的投入还不够形成强势趋势，当前更需要先把节奏做稳。"],
                "risks": ["活跃率只有 19.0%，当前最大问题是节奏断档。", "算法 占比已经到 85.7%，存在结构性失衡，容易形成战术逃避。"],
                "opportunities": ["当前最值得放大的，是把已经有效的主轴学科继续做深。"],
                "strategy_bias": "维持一主一辅的资源结构，避免面面俱到。"
              },
              "battle_plan": {
                "main_objective": "在 阶段（2026-03-14 至 2026-03-27） 内把主轴任务做深，同时维持结构稳定。",
                "secondary_objectives": ["把高频任务从“做了很多”切换成“真正产出结果”。"],
                "resource_allocation": [{"target": "算法", "allocation_pct": 50, "reason": "主轴加码"}],
                "critical_tasks": [{"task": "算法冲刺", "focus": "推进关键结果。", "guardrail": "完成后记录结果。"}],
                "execution_rhythm": ["先保主轴，再给第二重点方向分配稳定时段。"],
                "anti_patterns": ["为了看起来努力而拉长低质量时长。"],
                "next_review_point": "执行 3 天后做第一次偏差检查"
              }
            }
            """,
            """
            {
              "diagnosis": {
                "core_judgement": "现在真正的问题不是总量不足，而是算法冲刺还没被提升到压倒性优先级。",
                "status_level": "yellow",
                "key_signals": ["算法与科研同时占主线，但算法的结果兑现速度还没被真正拉起来。"],
                "risks": ["如果继续平均用力，下一周期仍会忙，但最关键的考试向目标不会明显前进。"],
                "opportunities": ["算法刷题和科研输入都已有基础，适合直接转成更强的主线推进。"],
                "strategy_bias": "把最好的时段优先让给算法冲刺，科研保主线，其他任务全部压缩。"
              },
              "battle_plan": {
                "main_objective": "下一周期优先把算法冲刺推到可见结果，同时只保留科研主线输入。",
                "secondary_objectives": ["压缩边缘任务，避免主线再次失焦。"],
                "resource_allocation": [{"target": "算法", "allocation_pct": 60, "reason": "考试压力最近且结果导向最强"}],
                "critical_tasks": [{"task": "算法冲刺", "focus": "把真题和限时模拟排成连续输出，不再停留在熟悉题区。", "guardrail": "单日低于目标时长立即补额。"}],
                "execution_rhythm": ["周前半段先冲算法，科研只做必要输入。"],
                "anti_patterns": ["不要再把时间耗在看起来充实但不推动结果的边缘任务上。"],
                "next_review_point": "执行 3 天后做第一次偏差检查"
              }
            }
            """,
        ]
        resp = client.post(
            "/api/ai/briefing",
            json={"scope": "stage", "stage_id": stage.id},
            headers=auth_headers(token),
        )

    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert mock_qwen.call_count == 2
    assert data["diagnosis"]["core_judgement"].startswith("现在真正的问题不是总量不足")
    assert "算法冲刺" in data["diagnosis"]["core_judgement"]
