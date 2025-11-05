"""
Leaderboard API blueprint
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.leaderboard_service import (
    get_leaderboard_rankings,
    get_user_public_stats,
    is_user_opted_in,
    set_leaderboard_opt_in,
)

bp = Blueprint("leaderboard", __name__)


@bp.route("/status", methods=["GET"])
@jwt_required()
def get_status():
    user_id = get_jwt_identity()
    return jsonify({"success": True, "data": {"opted_in": is_user_opted_in(user_id)}})


@bp.route("/join", methods=["POST"])
@jwt_required()
def join_leaderboard():
    user_id = get_jwt_identity()
    set_leaderboard_opt_in(user_id, True)
    return jsonify({"success": True, "message": "已加入社区排行"})


@bp.route("/leave", methods=["POST"])
@jwt_required()
def leave_leaderboard():
    user_id = get_jwt_identity()
    set_leaderboard_opt_in(user_id, False)
    return jsonify({"success": True, "message": "已退出社区排行"})


@bp.route("", methods=["GET"])
@bp.route("/", methods=["GET"])
@jwt_required()
def get_rankings():
    user_id = get_jwt_identity()
    period = request.args.get("period", "week").lower()
    metric = request.args.get("metric", "duration").lower()
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))

    try:
        result = get_leaderboard_rankings(
            requesting_user_id=user_id,
            period=period,
            metric=metric,
            page=page,
            page_size=page_size,
        )
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400

    return jsonify(result), 200


@bp.route("/users/<int:target_user_id>", methods=["GET"])
@jwt_required()
def get_public_stats(target_user_id: int):
    period = request.args.get("period", "week").lower()
    try:
        result = get_user_public_stats(target_user_id, period)
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400

    if not result:
        return jsonify({"success": False, "message": "用户未参与社区排行"}), 404

    return jsonify(result), 200
