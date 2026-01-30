from CTFd.plugins import register_plugin_assets_directory

def load(app):
    # Import routes
    from .routes import admin_bp
    
    # Register blueprints
    app.register_blueprint(admin_bp)
    
    # Register assets directory
    register_plugin_assets_directory(
        app, base_path='/plugins/challenge_deployer/assets/'
    )
