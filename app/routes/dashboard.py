from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.ticket import Ticket
from app.models.user import User


dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/api/dashboard"
)


@dashboard_bp.route("/summary", methods=["GET"])
@jwt_required()
def dashboard_summary():
    current_user_id = get_jwt_identity()

    current_user = db.session.get(User, int(current_user_id))

    if not current_user:
        return jsonify({
            "error": "User not found"
        }), 404

    if current_user.role not in ["agent", "admin"]:
        return jsonify({
            "error": "Access denied"
        }), 403

    total_tickets = Ticket.query.count()

    open_tickets = Ticket.query.filter_by(
        status="OPEN"
    ).count()

    in_progress_tickets = Ticket.query.filter_by(
        status="IN_PROGRESS"
    ).count()

    resolved_tickets = Ticket.query.filter_by(
        status="RESOLVED"
    ).count()

    closed_tickets = Ticket.query.filter_by(
        status="CLOSED"
    ).count()

    high_priority_tickets = Ticket.query.filter_by(
        priority="HIGH"
    ).count()

    return jsonify({
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "in_progress_tickets": in_progress_tickets,
        "resolved_tickets": resolved_tickets,
        "closed_tickets": closed_tickets,
        "high_priority_tickets": high_priority_tickets
    }), 200


@dashboard_bp.route("/statistics", methods=["GET"])
@jwt_required()
def ticket_statistics():
    current_user_id = get_jwt_identity()

    current_user = db.session.get(User, int(current_user_id))

    if not current_user:
        return jsonify({
            "error": "User not found"
        }), 404

    if current_user.role not in ["agent", "admin"]:
        return jsonify({
            "error": "Access denied"
        }), 403

    tickets = Ticket.query.all()

    by_status = {}
    by_priority = {}
    by_category = {}

    for ticket in tickets:
        by_status[ticket.status] = (
            by_status.get(ticket.status, 0) + 1
        )

        by_priority[ticket.priority] = (
            by_priority.get(ticket.priority, 0) + 1
        )

        category = ticket.category or "Uncategorized"

        by_category[category] = (
            by_category.get(category, 0) + 1
        )

    return jsonify({
        "by_status": by_status,
        "by_priority": by_priority,
        "by_category": by_category
    }), 200


@dashboard_bp.route("/agent-workload", methods=["GET"])
@jwt_required()
def agent_workload():
    current_user_id = get_jwt_identity()

    current_user = db.session.get(User, int(current_user_id))

    if not current_user:
        return jsonify({
            "error": "User not found"
        }), 404

    if current_user.role not in ["agent", "admin"]:
        return jsonify({
            "error": "Access denied"
        }), 403

    agents = User.query.filter_by(role="agent").all()

    workload = []

    for agent in agents:
        total_tickets = Ticket.query.filter_by(
            agent_id=agent.id
        ).count()

        open_tickets = Ticket.query.filter_by(
            agent_id=agent.id,
            status="OPEN"
        ).count()

        in_progress_tickets = Ticket.query.filter_by(
            agent_id=agent.id,
            status="IN_PROGRESS"
        ).count()

        resolved_tickets = Ticket.query.filter_by(
            agent_id=agent.id,
            status="RESOLVED"
        ).count()

        closed_tickets = Ticket.query.filter_by(
            agent_id=agent.id,
            status="CLOSED"
        ).count()

        workload.append({
            "agent_id": agent.id,
            "agent_name": agent.name,
            "email": agent.email,
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "in_progress_tickets": in_progress_tickets,
            "resolved_tickets": resolved_tickets,
            "closed_tickets": closed_tickets
        })

    return jsonify({
        "agents": workload
    }), 200


@dashboard_bp.route("/recent-tickets", methods=["GET"])
@jwt_required()
def recent_tickets():
    current_user_id = get_jwt_identity()

    current_user = db.session.get(User, int(current_user_id))

    if not current_user:
        return jsonify({
            "error": "User not found"
        }), 404

    if current_user.role not in ["agent", "admin"]:
        return jsonify({
            "error": "Access denied"
        }), 403

    limit = request.args.get("limit", default=5, type=int)

    if limit <= 0:
        return jsonify({
            "error": "limit must be greater than 0"
        }), 400

    if limit > 100:
        limit = 100

    tickets = (
        Ticket.query
        .order_by(Ticket.created_at.desc())
        .limit(limit)
        .all()
    )

    recent_tickets = []

    for ticket in tickets:
        recent_tickets.append({
            "id": ticket.id,
            "title": ticket.title,
            "status": ticket.status,
            "priority": ticket.priority,
            "category": ticket.category,
            "customer": (
                {
                    "id": ticket.customer.id,
                    "name": ticket.customer.name,
                    "email": ticket.customer.email
                }
                if ticket.customer
                else None
            ),
            "agent": (
                {
                    "id": ticket.agent.id,
                    "name": ticket.agent.name,
                    "email": ticket.agent.email
                }
                if ticket.agent
                else None
            ),
            "created_at": (
                ticket.created_at.isoformat()
                if ticket.created_at
                else None
            )
        })

    return jsonify({
        "tickets": recent_tickets,
        "count": len(recent_tickets)
    }), 200


@dashboard_bp.route("/tickets", methods=["GET"])
@jwt_required()
def filter_tickets():
    current_user_id = get_jwt_identity()

    current_user = db.session.get(User, int(current_user_id))

    if not current_user:
        return jsonify({
            "error": "User not found"
        }), 404

    if current_user.role not in ["agent", "admin"]:
        return jsonify({
            "error": "Access denied"
        }), 403

    status = request.args.get("status")
    priority = request.args.get("priority")
    category = request.args.get("category")
    agent_id = request.args.get("agent_id", type=int)
    search = request.args.get("search")

    limit = request.args.get(
        "limit",
        default=20,
        type=int
    )

    if limit <= 0:
        return jsonify({
            "error": "limit must be greater than 0"
        }), 400

    if limit > 100:
        limit = 100

    query = Ticket.query

    if status:
        query = query.filter(
            Ticket.status == status
        )

    if priority:
        query = query.filter(
            Ticket.priority == priority
        )

    if category:
        query = query.filter(
            Ticket.category == category
        )

    if agent_id:
        query = query.filter(
            Ticket.agent_id == agent_id
        )

    if search:
        search_term = f"%{search}%"

        query = query.filter(
            db.or_(
                Ticket.title.ilike(search_term),
                Ticket.description.ilike(search_term)
            )
        )

    tickets = (
        query
        .order_by(Ticket.created_at.desc())
        .limit(limit)
        .all()
    )

    result = []

    for ticket in tickets:
        result.append({
            "id": ticket.id,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status,
            "priority": ticket.priority,
            "category": ticket.category,
            "customer": (
                {
                    "id": ticket.customer.id,
                    "name": ticket.customer.name,
                    "email": ticket.customer.email
                }
                if ticket.customer
                else None
            ),
            "agent": (
                {
                    "id": ticket.agent.id,
                    "name": ticket.agent.name,
                    "email": ticket.agent.email
                }
                if ticket.agent
                else None
            ),
            "created_at": (
                ticket.created_at.isoformat()
                if ticket.created_at
                else None
            ),
            "updated_at": (
                ticket.updated_at.isoformat()
                if ticket.updated_at
                else None
            )
        })

    return jsonify({
        "count": len(result),
        "tickets": result
    }), 200
