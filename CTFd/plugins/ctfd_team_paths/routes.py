from flask import Blueprint, render_template, request, jsonify, abort
from CTFd.utils.user import get_current_user, get_current_team, authed
from CTFd.utils.decorators import authed_only
from CTFd.models import db
from .models import TreasurePath, TeamPathAssignment
from .utils import get_team_path, get_unlocked_challenges_for_path, get_path_challenges

team_paths_bp = Blueprint("team_paths", __name__, template_folder="templates")

@team_paths_bp.route("/api/v1/team-path/current", methods=["GET"])
@authed_only
def get_current_path_api():
    team = get_current_team()
    if not team:
        return jsonify({"success": False, "error": "You are not in a team"})

    path = get_team_path(team.id)
    if not path:
        return jsonify({"success": True, "data": None})

    unlocked_ids = get_unlocked_challenges_for_path(path, team.id)
    total_stages = len(get_path_challenges(path.id))
    current_stage = len(unlocked_ids)
    if current_stage > total_stages:
        current_stage = total_stages

    return jsonify({
        "success": True,
        "data": {
            "team": team.name,
            "path_name": path.name,
            "path_description": path.description,
            "color": path.color,
            "current_stage": current_stage,
            "total_stages": total_stages
        }
    })

@team_paths_bp.route("/team-path/assign", methods=["POST"])
@authed_only
def assign_team_path():
    team = get_current_team()
    if not team:
        return jsonify({"success": False, "error": "You must be in a team to join a path."}), 400

    existing = get_team_path(team.id)
    if existing:
        return jsonify({"success": False, "error": "Your team already has an assigned path."}), 400

    data = request.get_json()
    token = data.get("token")
    if not token:
        return jsonify({"success": False, "error": "Token required."}), 400

    path = TreasurePath.query.filter_by(token=token).first()
    if not path:
        return jsonify({"success": False, "error": "Invalid token."}), 400

    assignment = TeamPathAssignment(team_id=team.id, path_id=path.id)
    db.session.add(assignment)
    db.session.commit()

    return jsonify({"success": True, "message": f"Successfully assigned to {path.name}"})
