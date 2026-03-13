"""
AI assistant endpoints for analysis and planning.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services.ai_planner_service import (
    AIPlannerError,
    create_chat_message,
    generate_analysis,
    generate_briefing,
    generate_plan,
    list_chat_messages,
    list_chat_sessions,
    list_history,
)

bp = Blueprint("ai", __name__)


def _parse_request_payload():
    payload = request.get_json(silent=True) or {}
    scope = str(payload.get("scope") or "").lower()
    if scope not in {"day", "week", "month", "stage"}:
        raise AIPlannerError("scope 需要是 day/week/month/stage 之一")

    date_value = payload.get("date")
    date_str = None
    if date_value is not None:
        date_str = str(date_value).strip()
        if not date_str:
            date_str = None

    stage_value = payload.get("stage_id")
    stage_id = None
    if stage_value not in (None, ""):
        if isinstance(stage_value, (int, str)):
            try:
                stage_id = int(stage_value)
            except ValueError:
                raise AIPlannerError("stage_id 需要为整数")
        else:
            raise AIPlannerError("stage_id 需要为整数")

    return scope, date_str, stage_id


def _parse_chat_request_payload():
    payload = request.get_json(silent=True) or {}
    scope = str(payload.get("scope") or "global").lower()
    if scope not in {"global", "day", "week", "month", "stage"}:
        raise AIPlannerError("scope 需要是 global/day/week/month/stage 之一")

    date_value = payload.get("date")
    date_str = None
    if date_value is not None:
        date_str = str(date_value).strip() or None

    stage_value = payload.get("stage_id")
    stage_id = None
    if stage_value not in (None, ""):
        try:
            stage_id = int(stage_value)
        except (TypeError, ValueError):
            raise AIPlannerError("stage_id 需要为整数")

    session_value = payload.get("session_id")
    session_id = None
    if session_value not in (None, ""):
        try:
            session_id = int(session_value)
        except (TypeError, ValueError):
            raise AIPlannerError("session_id 需要为整数")

    content = str(payload.get("content") or "").strip()
    if not content:
        raise AIPlannerError("content 不能为空")

    return session_id, scope, date_str, stage_id, content


@bp.route("/analysis", methods=["POST"])
@jwt_required()
def create_analysis():
    user_id = get_jwt_identity()
    try:
        scope, date_str, stage_id = _parse_request_payload()
        result = generate_analysis(user_id, scope, date_str, stage_id)
        return jsonify({"success": True, "data": result}), 200
    except AIPlannerError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


@bp.route("/briefing", methods=["POST"])
@jwt_required()
def create_briefing():
    user_id = get_jwt_identity()
    try:
        scope, date_str, stage_id = _parse_request_payload()
        result = generate_briefing(user_id, scope, date_str, stage_id)
        return jsonify({"success": True, "data": result}), 200
    except AIPlannerError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


@bp.route("/plan", methods=["POST"])
@jwt_required()
def create_plan():
    user_id = get_jwt_identity()
    try:
        scope, date_str, stage_id = _parse_request_payload()
        result = generate_plan(user_id, scope, date_str, stage_id)
        return jsonify({"success": True, "data": result}), 200
    except AIPlannerError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


@bp.route("/history", methods=["GET"])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()

    try:
        limit = int(request.args.get("limit", 20))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "limit 参数必须为整数"}), 400

    try:
        offset = int(request.args.get("offset", 0))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "offset 参数必须为整数"}), 400

    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    scope = request.args.get("scope")
    if scope:
        scope = scope.lower()
        if scope not in {"day", "week", "month", "stage"}:
            return jsonify({"success": False, "message": "scope 参数无效"}), 400
    else:
        scope = None

    insight_type = request.args.get("type")
    if insight_type:
        insight_type = insight_type.lower()
        if insight_type not in {"analysis", "plan", "briefing"}:
            return jsonify({"success": False, "message": "type 参数无效"}), 400
    else:
        insight_type = None

    data = list_history(
        user_id,
        limit=limit,
        offset=offset,
        scope=scope,
        insight_type=insight_type,
    )
    return jsonify({"success": True, "data": data}), 200


@bp.route("/chat/messages", methods=["POST"])
@jwt_required()
def send_chat_message():
    user_id = get_jwt_identity()
    try:
        session_id, scope, date_str, stage_id, content = _parse_chat_request_payload()
        data = create_chat_message(
            user_id,
            session_id=session_id,
            scope=scope,
            date_str=date_str,
            stage_id=stage_id,
            content=content,
        )
        return jsonify({"success": True, "data": data}), 200
    except AIPlannerError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


@bp.route("/chat/sessions", methods=["GET"])
@jwt_required()
def get_chat_sessions():
    user_id = get_jwt_identity()
    return jsonify({"success": True, "data": list_chat_sessions(user_id)}), 200


@bp.route("/chat/sessions/<int:session_id>/messages", methods=["GET"])
@jwt_required()
def get_chat_messages(session_id: int):
    user_id = get_jwt_identity()
    try:
        data = list_chat_messages(user_id, session_id)
        return jsonify({"success": True, "data": data}), 200
    except AIPlannerError as exc:
        return jsonify({"success": False, "message": str(exc)}), 404
