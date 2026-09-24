from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.ticket import Ticket
from app.models.user import User
from app.models.comment import TicketComment
from app.models.notification import Notification


ticket_bp = Blueprint(
    "tickets",
    __name__,
    url_prefix="/api/tickets"
)


@ticket_bp.post("")
@jwt_required()
def create_ticket():
    user_id = int(get_jwt_identity())

    data = request.get_json() or {}

    title = data.get("title")
    description = data.get("description")
    category = data.get("category")
    priority = data.get("priority", "MEDIUM")

    if not title or not description:
        return jsonify({
            "error": "title and description are required"
        }), 400

    allowed_priorities = [
        "LOW",
        "MEDIUM",
        "HIGH",
        "URGENT"
    ]

    if priority not in allowed_priorities:
        return jsonify({
            "error": "Invalid priority"
        }), 400

    user = db.session.get(User, user_id)

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    ticket = Ticket(
        title=title,
        description=description,
        category=category,
        priority=priority,
        customer_id=user.id
    )

    db.session.add(ticket)
    db.session.commit()

    # Notify all agents about the new ticket
    agents = User.query.filter_by(role="agent").all()

    for agent in agents:
        notification = Notification(
            user_id=agent.id,
            title="New Ticket Created",
            message=f"New ticket #{ticket.id}: {ticket.title}",
            notification_type="ticket_created"
        )
        db.session.add(notification)

    db.session.commit()

    return jsonify({
        "message": "Ticket created successfully",
        "ticket": ticket.to_dict()
    }), 201


@ticket_bp.get("")
@jwt_required()
def get_tickets():
    user_id = int(get_jwt_identity())

    user = db.session.get(User, user_id)

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    if user.role == "customer":
        tickets = Ticket.query.filter_by(
            customer_id=user.id
        ).order_by(
            Ticket.created_at.desc()
        ).all()
    else:
        tickets = Ticket.query.order_by(
            Ticket.created_at.desc()
        ).all()

    return jsonify({
        "tickets": [
            ticket.to_dict()
            for ticket in tickets
        ]
    }), 200


@ticket_bp.get("/<int:ticket_id>")
@jwt_required()
def get_ticket(ticket_id):
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

    if user.role == "customer" and ticket.customer_id != user.id:
        return jsonify({
            "error": "Access denied"
        }), 403

    return jsonify({
        "ticket": ticket.to_dict()
    }), 200


@ticket_bp.patch("/<int:ticket_id>/assign")
@jwt_required()
def assign_ticket(ticket_id):
    user_id = int(get_jwt_identity())

    current_user = db.session.get(User, user_id)

    if not current_user:
        return jsonify({
            "error": "User not found"
        }), 404

    if current_user.role not in ["agent", "admin"]:
        return jsonify({
            "error": "Only agents and admins can assign tickets"
        }), 403

    ticket = db.session.get(Ticket, ticket_id)

    if not ticket:
        return jsonify({
            "error": "Ticket not found"
        }), 404

    data = request.get_json() or {}

    agent_id = data.get("agent_id")

    if not agent_id:
        return jsonify({
            "error": "agent_id is required"
        }), 400

    agent = db.session.get(User, int(agent_id))

    if not agent:
        return jsonify({
            "error": "Agent not found"
        }), 404

    if agent.role != "agent":
        return jsonify({
            "error": "Selected user is not an agent"
        }), 400

    ticket.agent_id = agent.id

    if ticket.status == "OPEN":
        ticket.status = "ASSIGNED"

    db.session.commit()

    return jsonify({
        "message": "Ticket assigned successfully",
        "ticket": ticket.to_dict()
    }), 200


@ticket_bp.patch("/<int:ticket_id>/status")
@jwt_required()
def update_ticket_status(ticket_id):
    user_id = int(get_jwt_identity())

    current_user = db.session.get(User, user_id)

    if not current_user:
        return jsonify({
            "error": "User not found"
        }), 404

    if current_user.role not in ["agent", "admin"]:
        return jsonify({
            "error": "Only agents and admins can update ticket status"
        }), 403

    ticket = db.session.get(Ticket, ticket_id)

    if not ticket:
        return jsonify({
            "error": "Ticket not found"
        }), 404

    if current_user.role == "agent" and ticket.agent_id != current_user.id:
        return jsonify({
            "error": "You can only update tickets assigned to you"
        }), 403

    data = request.get_json() or {}

    status = data.get("status")

    if not status:
        return jsonify({
            "error": "status is required"
        }), 400

    allowed_statuses = [
        "OPEN",
        "ASSIGNED",
        "IN_PROGRESS",
        "RESOLVED",
        "CLOSED"
    ]

    if status not in allowed_statuses:
        return jsonify({
            "error": "Invalid status"
        }), 400

    ticket.status = status

    db.session.commit()

    # Notify the customer about the status change
    notification = Notification(
        user_id=ticket.customer_id,
        title="Ticket Status Updated",
        message=f"Ticket #{ticket.id} status changed to {ticket.status}",
        notification_type="ticket_status_updated"
    )

    db.session.add(notification)
    db.session.commit()

    return jsonify({
        "message": "Ticket status updated successfully",
        "ticket": ticket.to_dict()
    }), 200


@ticket_bp.post("/<int:ticket_id>/comments")
@jwt_required()
def create_comment(ticket_id):
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

    if user.role == "customer" and ticket.customer_id != user.id:
        return jsonify({
            "error": "Access denied"
        }), 403

    if user.role == "agent" and ticket.agent_id != user.id:
        return jsonify({
            "error": "You can only comment on tickets assigned to you"
        }), 403

    data = request.get_json() or {}

    message = data.get("message")

    if not message or not message.strip():
        return jsonify({
            "error": "message is required"
        }), 400

    comment = TicketComment(
        ticket_id=ticket.id,
        user_id=user.id,
        message=message.strip()
    )

    db.session.add(comment)
    db.session.commit()

    # Notify the customer when an agent adds a comment
    if user.role == "agent":
        notification = Notification(
            user_id=ticket.customer_id,
            title="New Ticket Comment",
            message=f"Agent added a comment to ticket #{ticket.id}",
            notification_type="ticket_comment"
        )

        db.session.add(notification)
        db.session.commit()

    return jsonify({
        "message": "Comment added successfully",
        "comment": comment.to_dict()
    }), 201


@ticket_bp.get("/<int:ticket_id>/comments")
@jwt_required()
def get_comments(ticket_id):
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

    # Customers can only view comments on their own tickets
    if user.role == "customer" and ticket.customer_id != user.id:
        return jsonify({
            "error": "Access denied"
        }), 403

    # Agents can only view comments on tickets assigned to them
    if user.role == "agent" and ticket.agent_id != user.id:
        return jsonify({
            "error": "You can only view comments on tickets assigned to you"
        }), 403

    comments = TicketComment.query.filter_by(
        ticket_id=ticket.id
    ).order_by(
        TicketComment.created_at.asc()
    ).all()

    return jsonify({
        "ticket_id": ticket.id,
        "comments": [
            comment.to_dict()
            for comment in comments
        ]
    }), 200

