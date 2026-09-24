from flask import Flask
from flask_cors import CORS

from config.settings import Config
from app.extensions import db, jwt
from app.routes.health import health_bp
from app.routes.auth import auth_bp
from app.routes.ticket import ticket_bp
from app.routes.attachment import attachment_bp
from app.routes.dashboard import dashboard_bp
from app.routes.notification import notification_bp
from app.routes.admin import admin_bp

from app.models.user import User
from app.models.ticket import Ticket
from app.models.comment import TicketComment
from app.models.attachment import Attachment
from app.models.notification import Notification


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(ticket_bp)
    app.register_blueprint(attachment_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()

    return app

