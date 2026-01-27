from datetime import date

from app.models import Stage, Category, SubCategory, LogEntry


def test_create_record_stage_resolved_by_date(
    client, db_session, register_and_login, auth_headers
):
    token, user_id = register_and_login()

    stage_a = Stage(name="阶段A", start_date=date(2026, 1, 1), user_id=user_id)
    stage_b = Stage(name="阶段B", start_date=date(2026, 1, 18), user_id=user_id)
    db_session.session.add_all([stage_a, stage_b])

    category = Category(name="分类1", user_id=user_id)
    db_session.session.add(category)
    db_session.session.flush()
    subcategory = SubCategory(name="子类1", category_id=category.id)
    db_session.session.add(subcategory)
    db_session.session.commit()

    payload = {
        "task": "学习记录",
        "log_date": "2026-01-20",
        "subcategory_id": subcategory.id,
        "actual_duration": 60,
        # 模拟前端仍传当前阶段
        "stage_id": stage_a.id,
    }

    resp = client.post("/api/records", json=payload, headers=auth_headers(token))
    assert resp.status_code == 201

    record = LogEntry.query.first()
    assert record is not None
    assert record.stage_id == stage_b.id
