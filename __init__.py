from flask import Blueprint
from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import CHALLENGE_CLASSES
from CTFd.models import db

def load(app):
    app.db.create_all()
    
    # Register blueprint
    blueprint = Blueprint(
        'challenge_deployer',
        __name__,
        template_folder='templates',
        static_folder='assets',
        url_prefix='/challenge-deployer'
    )
    
    # Import routes
    from .routes import admin_bp
    
    # Register blueprints
    app.register_blueprint(admin_bp)
    
    # Register assets directory
    register_plugin_assets_directory(
        app, base_path='/challenge-deployer/assets/'
    )
