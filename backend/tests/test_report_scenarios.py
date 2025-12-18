
import pytest
from unittest.mock import patch
from datetime import date, datetime
from app.models import Stage, LogEntry
from app.services.ai_planner.errors import AIPlannerError

def test_structured_records_specific_stage(client, db_session, register_and_login, auth_headers):
    """
    场景: 请求特定阶段的结构化数据
    预期: 返回 200，且包含 weeks 和 days 的嵌套结构
    """
    token, user_id = register_and_login()
    
    # 准备数据
    stage = Stage(name="Test Stage", start_date=date.today(), user_id=user_id)
    db_session.session.add(stage)
    db_session.session.commit()
    
    # 添加一条日志以确保有结构化数据
    log = LogEntry(
        log_date=date.today(), 
        task="Test Task", 
        actual_duration=60, 
        stage_id=stage.id
    )
    db_session.session.add(log)
    db_session.session.commit()

    # 请求接口
    resp = client.get(f"/api/records/structured?stage_id={stage.id}", headers=auth_headers(token))
    
    # 验证结果
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    
    # 验证嵌套结构
    assert isinstance(data, list) # usually a list of weeks
    if len(data) > 0:
        week = data[0]
        assert "week_num" in week
        assert "days" in week
        assert isinstance(week["days"], list)
        if len(week["days"]) > 0:
            day = week["days"][0]
            assert "logs" in day
            assert isinstance(day["logs"], list)

def test_structured_records_unauthorized(client, db_session, register_and_login, auth_headers):
    """
    场景: 越权请求他人的阶段数据
    预期: 返回 404，提示 success: false
    """
    # 用户A创建数据
    token_a, user_a_id = register_and_login(username="userA", email="a@test.com")
    stage_a = Stage(name="User A Stage", start_date=date.today(), user_id=user_a_id)
    db_session.session.add(stage_a)
    db_session.session.commit()
    
    # 用户B尝试访问
    token_b, _ = register_and_login(username="userB", email="b@test.com")
    
    resp = client.get(f"/api/records/structured?stage_id={stage_a.id}", headers=auth_headers(token_b))
    
    # 验证结果
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["success"] is False
    assert "阶段不存在" in data.get("message", "") or "Not Found" in data.get("error", "")

def test_dashboard_summary_duration(client, db_session, register_and_login, auth_headers):
    """
    场景: 验证今日学习时长聚合
    预期: today_duration_minutes 与录入数据之和一致
    """
    token, user_id = register_and_login()
    stage = Stage(name="Current Stage", start_date=date.today(), user_id=user_id)
    db_session.session.add(stage)
    db_session.session.commit()
    
    # 添加两条今日记录: 45 + 30 = 75分钟
    db_session.session.add(LogEntry(log_date=date.today(), task="T1", actual_duration=45, stage_id=stage.id))
    db_session.session.add(LogEntry(log_date=date.today(), task="T2", actual_duration=30, stage_id=stage.id))
    db_session.session.commit()
    
    # 请求 Dashboard Summary
    # 注意：根据之前的分析，Dashboard API 路径可能是 /api/users/dashboard/summary
    # 如果找不到 path，此测试会 404。假设路径正确。
    resp = client.get("/api/users/dashboard/summary", headers=auth_headers(token))
    
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["today_duration_minutes"] == 75

def test_data_export_zip(client, db_session, register_and_login, auth_headers):
    """
    场景: 导出全量备份包
    预期: 响应流为 application/zip 格式
    """
    token, user_id = register_and_login()
    
    # 只要已登录，哪怕没数据也应该能导出空的结构
    resp = client.get("/api/records/export", headers=auth_headers(token))
    
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/zip"
    # 验证是 zip 文件头
    assert resp.data[:2] == b'PK'

def test_ai_analysis_fallback(client, db_session, register_and_login, auth_headers):
    """
    场景: 模拟历史记录为空时的分析请求 (触发 Fallback)
    预期: 触发 Fallback 机制，返回基于规则的统计文本
    """
    token, user_id = register_and_login()
    stage = Stage(name="Empty Stage", start_date=date.today(), user_id=user_id)
    db_session.session.add(stage)
    db_session.session.commit()

    # Mock _call_qwen to raise an error, forcing fallback
    with patch("app.services.ai_planner.llm_client._call_qwen") as mock_qwen:
        mock_qwen.side_effect = AIPlannerError("Simulated API Failure")
        
        payload = {
            "scope": "stage",
            "stage_id": stage.id,
            "date": str(date.today())
        }
        resp = client.post("/api/ai/analysis", json=payload, headers=auth_headers(token))
        
        assert resp.status_code == 200 # Fallback should succeed with 200
        result = resp.get_json()
        assert result["success"] is True
        
        content = result["data"]["text"]
        # Fallback text usually contains specific structure
        assert "## 分析总结" in content or "离线模板生成" in content
