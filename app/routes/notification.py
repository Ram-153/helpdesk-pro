from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.notification import Notification
from app.models.user import User


notification_bp = Blueprint(
    "notification",
    __name__,
    url_prefix="/api/notifications"
)


@notification_bp.route("", methods=["GET"])
@jwt_required()
def get_notifications():
    current_user_id = get_jwt_identity()

    current_user = db.session.get(User, int(current_user_id))

    if not current_user:
        return jsonify({
            "error": "User not found"
        }), 404

    notifications = (
        Notification.query
        .filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )

    return jsonify({
        "count": len(notifications),
        "notifications": [
            notification.to_dict()
            for notification in notifications
        ]
    }), 200


@notification_bp.route("/<int:notification_id>/read", methods=["PATCH"])
@jwt_required()
def mark_notification_read(notification_id):
    current_user_id = get_jwt_identity()

    current_user = db.session.get(User, int(current_user_id))

    if not current_user:
        return jsonify({
            "error": "User not found"
        }), 404

    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first()

    if not notification:
        return jsonify({
            "error": "Notification not found"
        }), 404

    notification.is_read = True

    db.session.commit()

    return jsonify({
        "message": "Notification marked as read",
        "notification": notification.to_dict()
    }), 200


@notification_bp.route("/read-all", methods=["PATCH"])
@jwt_required()
def mark_all_notifications_read():
    current_user_id = get_jwt_identity()

    current_user = db.session.get(User, int(current_user_id))

    if not current_user:
        return jsonify({
            "error": "User not found"
        }), 404

    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).all()

    for notification in notifications:
        notification.is_read = True

    db.session.commit()

    return jsonify({
        "message": "All notifications marked as read",
        "updated_count": len(notifications)
    }), 200