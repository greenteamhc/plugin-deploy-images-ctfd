def load(app):
    """Load the deploy_desafios plugin"""
    from .routes import deploy_bp
    
    # Register the blueprint
    app.register_blueprint(deploy_bp)
