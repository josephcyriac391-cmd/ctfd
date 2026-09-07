from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from CTFd.utils.decorators import admins_only
from CTFd.models import db, Teams, Challenges, Solves
from .models import TreasurePath, TeamPathAssignment, PathChallenge

admin_team_paths_bp = Blueprint("admin_team_paths", __name__, template_folder="templates")

@admin_team_paths_bp.route("/admin/team-paths", methods=["GET"])
@admins_only
def paths_overview():
    paths = TreasurePath.query.all()
    teams = Teams.query.filter_by(banned=False, hidden=False).all()
    assignments = TeamPathAssignment.query.all()
    
    return render_template(
        "admin/paths.html", 
        paths=paths, 
        teams=teams, 
        assignments=assignments
    )

@admin_team_paths_bp.route("/admin/team-paths/new", methods=["POST"])
@admins_only
def create_path():
    data = request.form
    name = data.get("name")
    if not name:
        return redirect(url_for("admin_team_paths.paths_overview"))
        
    path = TreasurePath(
        name=name,
        description=data.get("description", ""),
        color=data.get("color", ""),
        mode=data.get("mode", "strict"),
        token=data.get("token", None) or None
    )
    db.session.add(path)
    db.session.commit()
    return redirect(url_for("admin_team_paths.paths_overview"))

@admin_team_paths_bp.route("/admin/team-paths/<int:path_id>", methods=["GET", "POST"])
@admins_only
def path_detail(path_id):
    path = TreasurePath.query.get_or_404(path_id)
    if request.method == "POST":
        data = request.form
        path.name = data.get("name", path.name)
        path.description = data.get("description", path.description)
        path.color = data.get("color", path.color)
        path.mode = data.get("mode", path.mode)
        path.token = data.get("token", path.token) or None
        db.session.commit()
        return redirect(url_for("admin_team_paths.path_detail", path_id=path.id))
        
    challenges = Challenges.query.all()
    return render_template("admin/path_edit.html", path=path, challenges=challenges)

@admin_team_paths_bp.route("/api/v1/admin/team-paths/<int:path_id>/challenges", methods=["POST"])
@admins_only
def assign_challenge_to_path(path_id):
    path = TreasurePath.query.get_or_404(path_id)
    data = request.get_json()
    challenge_id = data.get("challenge_id")
    
    if not challenge_id:
        return jsonify({"success": False, "error": "Missing challenge_id"})
        
    existing = PathChallenge.query.filter_by(path_id=path_id, challenge_id=challenge_id).first()
    if existing:
        return jsonify({"success": False, "error": "Challenge already in path"})
        
    order = PathChallenge.query.filter_by(path_id=path_id).count() + 1
    pc = PathChallenge(path_id=path_id, challenge_id=challenge_id, stage_order=order)
    db.session.add(pc)
    db.session.commit()
    return jsonify({"success": True})

@admin_team_paths_bp.route("/api/v1/admin/team-paths/<int:path_id>/challenges/<int:challenge_id>", methods=["DELETE"])
@admins_only
def remove_challenge_from_path(path_id, challenge_id):
    pc = PathChallenge.query.filter_by(path_id=path_id, challenge_id=challenge_id).first()
    if pc:
        db.session.delete(pc)
        db.session.commit()
    return jsonify({"success": True})

@admin_team_paths_bp.route("/api/v1/admin/team-paths/<int:path_id>/reorder", methods=["POST"])
@admins_only
def reorder_challenges(path_id):
    data = request.get_json()
    challenge_ids = data.get("challenge_ids", [])
    
    for i, cid in enumerate(challenge_ids):
        pc = PathChallenge.query.filter_by(path_id=path_id, challenge_id=cid).first()
        if pc:
            pc.stage_order = i + 1
            
    db.session.commit()
    return jsonify({"success": True})

@admin_team_paths_bp.route("/api/v1/admin/team-paths/assign", methods=["POST"])
@admins_only
def assign_team():
    data = request.form
    team_id = data.get("team_id")
    path_id = data.get("path_id")
    
    if not team_id or not path_id:
        return redirect(url_for("admin_team_paths.paths_overview"))
        
    existing = TeamPathAssignment.query.filter_by(team_id=team_id).first()
    if existing:
        existing.path_id = path_id
    else:
        assignment = TeamPathAssignment(team_id=team_id, path_id=path_id)
        db.session.add(assignment)
        
    db.session.commit()
    return redirect(url_for("admin_team_paths.paths_overview"))

@admin_team_paths_bp.route("/admin/team-paths/monitor", methods=["GET"])
@admins_only
def monitor_paths():
    return render_template("admin/monitoring.html")

@admin_team_paths_bp.route("/api/v1/admin/team-paths/monitor", methods=["GET"])
@admins_only
def monitor_api():
    assignments = TeamPathAssignment.query.all()
    results = []
    
    for a in assignments:
        solves = Solves.query.filter_by(team_id=a.team_id).all()
        solved_ids = [s.challenge_id for s in solves]
        
        path_chals = PathChallenge.query.filter_by(path_id=a.path_id).all()
        path_chal_ids = [p.challenge_id for p in path_chals]
        
        completed = len(set(solved_ids).intersection(set(path_chal_ids)))
        last_solve = max([s.date for s in solves]) if solves else None
        
        results.append({
            "team": a.team.name,
            "path": a.path.name,
            "completed": completed,
            "total": len(path_chals),
            "last_solve": last_solve.isoformat() if last_solve else "None",
            "score": a.team.score
        })
        
    return jsonify({"success": True, "data": results})
