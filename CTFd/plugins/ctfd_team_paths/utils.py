from CTFd.models import Solves, Challenges
from CTFd.utils.user import get_current_user, get_current_team, is_admin
from CTFd.utils import config
from .models import TreasurePath, TeamPathAssignment, PathChallenge

def get_team_path(team_id):
    assignment = TeamPathAssignment.query.filter_by(team_id=team_id).first()
    if assignment:
        return assignment.path
    return None

def get_path_challenges(path_id):
    return PathChallenge.query.filter_by(path_id=path_id).order_by(PathChallenge.stage_order).all()

def is_challenge_global(challenge_id):
    # A challenge is global if it is not associated with any path
    count = PathChallenge.query.filter_by(challenge_id=challenge_id).count()
    return count == 0

def get_unlocked_challenges_for_path(path, team_id):
    path_chals = get_path_challenges(path.id)
    if path.mode != "strict":
        # Free mode: all challenges in this path are unlocked
        return [pc.challenge_id for pc in path_chals]

    # Strict mode: check solves
    solved_challenge_ids = set([
        s.challenge_id for s in Solves.query.filter_by(team_id=team_id).all()
    ])
    
    unlocked = []
    # If a team hasn't solved the 1st, they only see the 1st.
    # If they solved 1st, they see 1st and 2nd, etc.
    for i, pc in enumerate(path_chals):
        unlocked.append(pc.challenge_id)
        if pc.challenge_id not in solved_challenge_ids:
            # Stop unlocking further challenges since this one isn't solved
            break
            
    return unlocked

def filter_challenge_data_for_user(data, user, team):
    if is_admin():
        return data

    if not config.is_teams_mode():
        # This plugin is designed for teams mode, if not in teams mode, allow all or hide all?
        # Let's just allow all or hide path challenges. Let's hide all path challenges for non-teams.
        return [c for c in data if is_challenge_global(c['id'])]

    if not team:
        return [c for c in data if is_challenge_global(c['id'])]

    path = get_team_path(team.id)
    if not path:
        return [c for c in data if is_challenge_global(c['id'])]

    unlocked_ids = get_unlocked_challenges_for_path(path, team.id)

    filtered = []
    for c in data:
        c_id = c['id']
        if is_challenge_global(c_id):
            filtered.append(c)
        elif c_id in unlocked_ids:
            filtered.append(c)
            
    return filtered

def can_access_specific_challenge(challenge_id, user, team):
    if is_admin():
        return True

    if is_challenge_global(challenge_id):
        return True

    if not config.is_teams_mode() or not team:
        return False

    path = get_team_path(team.id)
    if not path:
        return False

    unlocked_ids = get_unlocked_challenges_for_path(path, team.id)
    return challenge_id in unlocked_ids
