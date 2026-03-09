"""Category merge endpoint tests."""

from datetime import date

from app.models import Stage, Category, SubCategory, LogEntry


def _auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def _register_and_login(client, username: str, email: str):
    client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": "pw123"},
    )
    login_resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": "pw123"},
    )
    payload = login_resp.get_json()
    return payload["access_token"], payload["user"]["id"]


def test_merge_subcategory_success(client, db_session):
    token, user_id = _register_and_login(client, "merge_u1", "merge_u1@test.com")

    category = Category(name="分类A", user_id=user_id)
    db_session.session.add(category)
    db_session.session.flush()

    source_sub = SubCategory(name="子分类A", category_id=category.id)
    target_sub = SubCategory(name="子分类B", category_id=category.id)
    db_session.session.add_all([source_sub, target_sub])
    db_session.session.flush()

    stage = Stage(name="阶段1", start_date=date.today(), user_id=user_id)
    db_session.session.add(stage)
    db_session.session.flush()

    record = LogEntry(
        log_date=date.today(),
        task="测试合并",
        actual_duration=30,
        stage_id=stage.id,
        subcategory_id=source_sub.id,
    )
    db_session.session.add(record)
    db_session.session.commit()

    resp = client.post(
        f"/api/categories/subcategories/{source_sub.id}/merge",
        json={"target_subcategory_id": target_sub.id},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["moved_records"] == 1

    merged_record = LogEntry.query.filter_by(id=record.id).first()
    assert merged_record is not None
    assert merged_record.subcategory_id == target_sub.id
    assert SubCategory.query.filter_by(id=source_sub.id).first() is None
    assert SubCategory.query.filter_by(id=target_sub.id).first() is not None


def test_merge_subcategory_to_self_rejected(client, db_session):
    token, user_id = _register_and_login(client, "merge_u2", "merge_u2@test.com")

    category = Category(name="分类A", user_id=user_id)
    db_session.session.add(category)
    db_session.session.flush()

    source_sub = SubCategory(name="子分类A", category_id=category.id)
    db_session.session.add(source_sub)
    db_session.session.commit()

    resp = client.post(
        f"/api/categories/subcategories/{source_sub.id}/merge",
        json={"target_subcategory_id": source_sub.id},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False


def test_merge_subcategory_target_not_owned_returns_404(client, db_session):
    token_a, user_id_a = _register_and_login(client, "merge_u3a", "merge_u3a@test.com")
    token_b, user_id_b = _register_and_login(client, "merge_u3b", "merge_u3b@test.com")

    category_a = Category(name="分类A", user_id=user_id_a)
    db_session.session.add(category_a)
    db_session.session.flush()
    source_sub = SubCategory(name="来源标签", category_id=category_a.id)
    db_session.session.add(source_sub)

    category_b = Category(name="分类B", user_id=user_id_b)
    db_session.session.add(category_b)
    db_session.session.flush()
    target_sub = SubCategory(name="目标标签", category_id=category_b.id)
    db_session.session.add(target_sub)
    db_session.session.commit()

    resp = client.post(
        f"/api/categories/subcategories/{source_sub.id}/merge",
        json={"target_subcategory_id": target_sub.id},
        headers=_auth_headers(token_a),
    )
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["success"] is False

    # 确保未发生删除
    assert SubCategory.query.filter_by(id=source_sub.id).first() is not None
    assert SubCategory.query.filter_by(id=target_sub.id).first() is not None
