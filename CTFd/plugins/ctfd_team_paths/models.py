from CTFd.models import db

class TreasurePath(db.Model):
    __tablename__ = "treasure_paths"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(32), nullable=True)
    mode = db.Column(db.String(32), default="strict") # strict or free
    token = db.Column(db.String(64), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now())

    teams = db.relationship("TeamPathAssignment", back_populates="path", cascade="all, delete-orphan")
    challenges = db.relationship("PathChallenge", back_populates="path", cascade="all, delete-orphan", order_by="PathChallenge.stage_order")

class TeamPathAssignment(db.Model):
    __tablename__ = "team_path_assignments"
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id", ondelete="CASCADE"))
    path_id = db.Column(db.Integer, db.ForeignKey("treasure_paths.id", ondelete="CASCADE"))
    assigned_at = db.Column(db.DateTime, default=db.func.now())

    team = db.relationship("Teams", foreign_keys="TeamPathAssignment.team_id")
    path = db.relationship("TreasurePath", back_populates="teams")

class PathChallenge(db.Model):
    __tablename__ = "path_challenges"
    id = db.Column(db.Integer, primary_key=True)
    path_id = db.Column(db.Integer, db.ForeignKey("treasure_paths.id", ondelete="CASCADE"))
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE"))
    stage_order = db.Column(db.Integer, nullable=False, default=1)

    path = db.relationship("TreasurePath", back_populates="challenges")
    challenge = db.relationship("Challenges", foreign_keys="PathChallenge.challenge_id")
