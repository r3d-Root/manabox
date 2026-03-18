from flask import Flask
from .extensions import db, oauth, smorest_api

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    oauth.init_app(app)
    smorest_api.init_app(app)

    from .auth.routes import auth_bp
    from .web.routes import web_bp
    from .api.routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(web_bp)
    smorest_api.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()

    return app