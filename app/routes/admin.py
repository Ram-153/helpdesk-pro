from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.user import User
from app.models.ticket import Ticket
from app.models.notification import Notification


admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/api/admin"
)


@admin_bp.get("/users")
@jwt_required()
def get_all_users():
    user_id = int(get_jwt_identity())

    current_user = db.session.get(User, user_id)

    if not current_user:
        return jsonify({
            "error": "User not found"
        }), 404

    if current_user.role != "admin":
        return jsonify({
            "error": "Admin access required"
        }), 403

    users = User.query.order_by(User.id.asc()).all()

    return jsonify({
        "count": len(users),
        "users": [user.to_dict() for user in users]
    }), 200


@admin_bp.post("/users")
@jwt_required()
def create_user():
    user_id = int(get_jwt_identity())

    current_user = db.session.get(User, user_id)

    if not current_user:
        return jsonify({
            "error": "User not found"
        }), 404

    if current_user.role != "admin":
        return jsonify({
            "error": "Admin access required"
        }), 403

    data = request.get_json() or {}

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")

    if not name or not email or not password or not role:
        return jsonify({
            "error": "name, email, password and role are required"
        }), 400

    if role not in ["customer", "agent"]:
        return jsonify({
            "error": "Role must be customer or agent"
        }), 400

    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        return jsonify({
            "error": "Email already registered"
        }), 409

    new_user = User(
        name=name,
        email=email,
        role=role
    )

    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "User created successfully",
        "user": new_user.to_dict()
    }), 201


@admin_bp.get("/users/<int:user_id>")
@jwt_required()
def get_single_user(user_id):
    admin_id = int(get_jwt_identity())

    current_user = db.session.get(User, admin_id)

    if not current_user:
        return jsonify({
            "error": "User not found"
        }), 404

    if current_user.role != "admin":
        return jsonify({
            "error": "Admin access required"
        }), 403

    user = db.session.get(User, user_id)

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    return jsonify({
        "user": user.to_dict()
    }), 200


@admin_bp.patch("/users/<int:user_id>/role")
@jwt_required()
def change_user_role(user_id):
    admin_id = int(get_jwt_identity())

    current_user = db.session.get(User, admin_id)

    if not current_user:
        return jsonify({
            "error": "User not found"
        }), 404

    if current_user.role != "admin":
        return jsonify({
            "error": "Admin access required"
        }), 403

    user = db.session.get(User, user_id)

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    data = request.get_json() or {}

    new_role = data.get("role")

    if not new_role:
        return jsonify({
            "error": "role is required"
        }), 400

    if new_role not in ["customer", "agent"]:
        return jsonify({
            "error": "Role must be customer or agent"
        }), 400

    if user.role == new_role:
        return jsonify({
            "error": f"User is already a {new_role}"
        }), 400

    user.role = new_role

    db.session.commit()

    return jsonify({
        "message": "User role updated successfully",
        "user": user.to_dict()
    }), 200


@admin_bp.patch("/users/<int:user_id>/status")
@jwt_required()
def change_user_status(user_id):
    admin_id = int(get_jwt_identity())

    current_user = db.session.get(User, admin_id)

    if not current_user:
        return jsonify({
            "error": "User not found"
        }), 404

    if current_user.role != "admin":
        return jsonify({
            "error": "Admin access required"
        }), 403

    user = db.session.get(User, user_id)

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    data = request.get_json() or {}

    if "is_active" not in data:
        return jsonify({
            "error": "is_active is required"
        }), 400

    is_active = data.get("is_active")

    if not isinstance(is_active, bool):
        return jsonify({
            "error": "is_active must be true or false"
        }), 400

    if user.id == admin_id and is_active is False:
        return jsonify({
            "error": "Admin cannot deactivate their own account"
        }), 400

    user.is_active = is_active

    db.session.commit()

    status = "activated" if is_active else "deactivated"

    return jsonify({
        "message": f"User {status} successfully",
        "user": user.to_dict()
    }), 200


@admin_bp.get("/agents")
@jwt_required()
def get_all_agents():
    admin_id = int(get_jwt_identity())

    current_user = db.session.get(User, admin_id)

    if not current_user:
        return jsonify({
            "error": "User not found"
        }), 404

    if current_user.role != "admin":
        return jsonify({
            "error": "Admin access required"
        }), 403

    agents = User.query.filter_by(
        role="agent"
    ).order_by(
        User.id.asc()
    ).all()

    return jsonify({
        "count": len(agents),
        "agents": [agent.to_dict() for agent in agents]
    }), 200


@admin_bp.patch("/tickets/<int:ticket_id>/assign")
@jwt_required()
def admin_assign_ticket(ticket_id):
    admin_id = int(get_jwt_identity())

    current_user = db.session.get(User, admin_id)

    if not current_user:
        return jsonify({
            "error": "User not found"
        }), 404

    if current_user.role != "admin":
        return jsonify({
            "error": "Admin access required"
        }), 403

    ticket = db.session.get(Ticket, ticket_id)

    if not ticket:
        return jsonify({
            "error": "Ticket not found"
        }), 404

    data = request.get_json() or {}

    agent_id = data.get("agent_id")

    if agent_id is None:
        return jsonify({
            "error": "agent_id is required"
        }), 400

    try:
        agent_id = int(agent_id)
    except (TypeError, ValueError):
        return jsonify({
            "error": "agent_id must be a valid integer"
        }), 400

    agent = db.session.get(User, agent_id)

    if not agent:
        return jsonify({
            "error": "Agent not found"
        }), 404

    if agent.role != "agent":
        return jsonify({
            "error": "Selected user is not an agent"
        }), 400

    if not agent.is_active:
        return jsonify({
            "error": "Selected agent is inactive"
        }), 400

    if ticket.agent_id == agent.id:
        return jsonify({
            "error": "Ticket is already assigned to this agent"
        }), 400

    previous_agent_id = ticket.agent_id

    ticket.agent_id = agent.id

    if ticket.status == "OPEN":
        ticket.status = "ASSIGNED"

    notification = Notification(
        user_id=agent.id,
        title="Ticket Assigned",
        message=f"Ticket #{ticket.id} has been assigned to you",
        notification_type="ticket_assigned"
    )

    db.session.add(notification)
    db.session.commit()

    return jsonify({
        "message": "Ticket assigned successfully",
        "previous_agent_id": previous_agent_id,
        "ticket": ticket.to_dict()
    }), 200


@admin_bp.get("/stats")
@jwt_required()
def get_admin_stats():
    admin_id = int(get_jwt_identity())

    current_user = db.session.get(User, admin_id)

    if not current_user:
        return jsonify({
            "error": "User not found"
        }), 404

    if current_user.role != "admin":
        return jsonify({
            "error": "Admin access required"
        }), 403

    users = User.query.all()
    tickets = Ticket.query.all()

    total_users = len(users)
    total_customers = sum(
        1 for user in users
        if user.role == "customer"
    )
    total_agents = sum(
        1 for user in users
        if user.role == "agent"
    )
    total_admins = sum(
        1 for user in users
        if user.role == "admin"
    )

    active_users = sum(
        1 for user in users
        if user.is_active
    )
    inactive_users = sum(
        1 for user in users
        if not user.is_active
    )

    total_tickets = len(tickets)

    open_tickets = sum(
        1 for ticket in tickets
        if ticket.status == "OPEN"
    )
    assigned_tickets = sum(
        1 for ticket in tickets
        if ticket.status == "ASSIGNED"
    )
    in_progress_tickets = sum(
        1 for ticket in tickets
        if ticket.status == "IN_PROGRESS"
    )
    resolved_tickets = sum(
        1 for ticket in tickets
        if ticket.status == "RESOLVED"
    )
    closed_tickets = sum(
        1 for ticket in tickets
        if ticket.status == "CLOSED"
    )

    assigned_count = sum(
        1 for ticket in tickets
        if ticket.agent_id is not None
    )
    unassigned_count = sum(
        1 for ticket in tickets
        if ticket.agent_id is None
    )

    low_priority = sum(
        1 for ticket in tickets
        if ticket.priority == "LOW"
    )
    medium_priority = sum(
        1 for ticket in tickets
        if ticket.priority == "MEDIUM"
    )
    high_priority = sum(
        1 for ticket in tickets
        if ticket.priority == "HIGH"
    )
    urgent_priority = sum(
        1 for ticket in tickets
        if ticket.priority == "URGENT"
    )

    return jsonify({
        "users": {
            "total": total_users,
            "customers": total_customers,
            "agents": total_agents,
            "admins": total_admins,
            "active": active_users,
            "inactive": inactive_users
        },
        "tickets": {
            "total": total_tickets,
            "open": open_tickets,
            "assigned": assigned_tickets,
            "in_progress": in_progress_tickets,
            "resolved": resolved_tickets,
            "closed": closed_tickets,
            "assigned_count": assigned_count,
            "unassigned_count": unassigned_count
        },
        "priorities": {
            "low": low_priority,
            "medium": medium_priority,
            "high": high_priority,
            "urgent": urgent_priority
        }
    }), 200
