import os

from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.user import User
from app.models.ticket import Ticket
from app.models.attachment import Attachment
from app.services.attachment_service import save_attachment


attachment_bp = Blueprint(
    "attachments",
    __name__,
    url_prefix="/api"
)


UPLOAD_DIRECTORY = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "uploads",
        "tickets"
    )
)


def can_access_ticket(user, ticket):
    if user.role == "admin":
        return True

    if user.role == "customer":
        return ticket.customer_id == user.id

    if user.role == "agent":
        return ticket.agent_id == user.id

    return False


@attachment_bp.post("/tickets/<int:ticket_id>/attachments")
@jwt_required()
def upload_attachment(ticket_id):
    user_id = int(get_jwt_identity())

    user = db.session.get(User, user_id)

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    ticket = db.session.get(Ticket, ticket_id)

    if not ticket:
        return jsonify({
            "error": "Ticket not found"
        }), 404

    if not can_access_ticket(user, ticket):
        return jsonify({
            "error": "Access denied"
        }), 403

    if "file" not in request.files:
        return jsonify({
            "error": "No file provided"
        }), 400

    file = request.files["file"]

    try:
        file_data = save_attachment(
            file,
            UPLOAD_DIRECTORY
        )

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

    attachment = Attachment(
        ticket_id=ticket.id,
        uploaded_by=user.id,
        original_filename=file_data["original_filename"],
        stored_filename=file_data["stored_filename"],
        file_path=file_data["file_path"],
        mime_type=file_data["mime_type"],
        file_size=file_data["file_size"]
    )

    try:
        db.session.add(attachment)
        db.session.commit()

    except Exception:
        db.session.rollback()

        if os.path.exists(file_data["file_path"]):
            os.remove(file_data["file_path"])

        return jsonify({
            "error": "Failed to save attachment"
        }), 500

    return jsonify({
        "message": "Attachment uploaded successfully",
        "attachment": attachment.to_dict()
    }), 201


@attachment_bp.get("/tickets/<int:ticket_id>/attachments")
@jwt_required()
def get_ticket_attachments(ticket_id):
    user_id = int(get_jwt_identity())

    user = db.session.get(User, user_id)

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    ticket = db.session.get(Ticket, ticket_id)

    if not ticket:
        return jsonify({
            "error": "Ticket not found"
        }), 404

    if not can_access_ticket(user, ticket):
        return jsonify({
            "error": "Access denied"
        }), 403

    attachments = Attachment.query.filter_by(
        ticket_id=ticket.id
    ).order_by(
        Attachment.created_at.asc()
    ).all()

    return jsonify({
        "ticket_id": ticket.id,
        "attachments": [
            attachment.to_dict()
            for attachment in attachments
        ]
    }), 200


@attachment_bp.get("/attachments/<int:attachment_id>")
@jwt_required()
def download_attachment(attachment_id):
    user_id = int(get_jwt_identity())

    user = db.session.get(User, user_id)

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    attachment = db.session.get(
        Attachment,
        attachment_id
    )

    if not attachment:
        return jsonify({
            "error": "Attachment not found"
        }), 404

    ticket = db.session.get(
        Ticket,
        attachment.ticket_id
    )

    if not ticket:
        return jsonify({
            "error": "Ticket not found"
        }), 404

    if not can_access_ticket(user, ticket):
        return jsonify({
            "error": "Access denied"
        }), 403

    if not os.path.exists(attachment.file_path):
        return jsonify({
            "error": "Attachment file not found"
        }), 404

    return send_file(
        attachment.file_path,
        mimetype=attachment.mime_type,
        as_attachment=True,
        download_name=attachment.original_filename
    )


@attachment_bp.delete("/attachments/<int:attachment_id>")
@jwt_required()
def delete_attachment(attachment_id):
    user_id = int(get_jwt_identity())

    user = db.session.get(User, user_id)

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    attachment = db.session.get(
        Attachment,
        attachment_id
    )

    if not attachment:
        return jsonify({
            "error": "Attachment not found"
        }), 404

    ticket = db.session.get(
        Ticket,
        attachment.ticket_id
    )

    if not ticket:
        return jsonify({
            "error": "Ticket not found"
        }), 404

    if user.role not in ["agent", "admin"]:
        return jsonify({
            "error": "Only agents and admins can delete attachments"
        }), 403

    if user.role == "agent" and ticket.agent_id != user.id:
        return jsonify({
            "error": "You can only delete attachments from tickets assigned to you"
        }), 403

    if os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)

    db.session.delete(attachment)
    db.session.commit()

    return jsonify({
        "message": "Attachment deleted successfully"
    }), 200