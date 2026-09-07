from flask import abort, request
from CTFd.plugins import register_plugin_assets_directory, register_admin_plugin_menu_bar, register_plugin_script
from CTFd.api.v1.challenges import ChallengeList, Challenge
from CTFd.utils.user import get_current_user, get_current_team

from .models import TreasurePath, TeamPathAssignment, PathChallenge
from .utils import filter_challenge_data_for_user, can_access_specific_challenge
from .routes import team_paths_bp
from .admin import admin_team_paths_bp

def load(app):
    # Initialize Database Models
    app.db.create_all()

    # Register Blueprints
    app.register_blueprint(team_paths_bp)
    app.register_blueprint(admin_team_paths_bp)

    # Register Admin Menu Bar
    register_admin_plugin_menu_bar(title='Treasure Paths', route='/admin/team-paths')

    # Register Frontend Script (This injects the UI for users)
    register_plugin_assets_directory(app, base_path='/plugins/ctfd_team_paths/assets')
    register_plugin_script('/plugins/ctfd_team_paths/assets/js/team_paths.js')

    # --------------------------------------------------------------------------------
    # MONKEY PATCH CTFD CORE ENDPOINTS FOR CHALLENGE VISIBILITY
    # --------------------------------------------------------------------------------
    
    # Patch 1: ChallengeList GET (/api/v1/challenges)
    original_challenge_list_get = ChallengeList.get

    def custom_challenge_list_get(self, *args, **kwargs):
        # Call the original CTFd core function
        response = original_challenge_list_get(self, *args, **kwargs)
        
        # If it returns a tuple or response object directly (errors), return it
        if isinstance(response, tuple) or not isinstance(response, dict):
            return response
            
        if not response.get("success"):
            return response

        # Filter the returned data
        user = get_current_user()
        team = get_current_team()
        
        data = response.get("data", [])
        filtered_data = filter_challenge_data_for_user(data, user, team)
        
        response["data"] = filtered_data
        return response

    ChallengeList.get = custom_challenge_list_get

    # Patch 2: Challenge GET (/api/v1/challenges/<id>)
    original_challenge_get = Challenge.get

    def custom_challenge_get(self, challenge_id, *args, **kwargs):
        # Check our plugin authorization first
        user = get_current_user()
        team = get_current_team()
        
        if not can_access_specific_challenge(challenge_id, user, team):
            abort(403)
            
        # Call the original CTFd core function if authorized
        return original_challenge_get(self, challenge_id, *args, **kwargs)

    Challenge.get = custom_challenge_get
