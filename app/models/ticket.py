from datetime import datetime, timezone

from app.extensions import db


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    description = db.Column(db.Text, nullable=False)

    status = db.Column(
        db.String(30),
        nullable=False,
        default="OPEN"
    )

    priority = db.Column(
        db.String(20),
        nullable=False,
        default="MEDIUM"
    )

    category = db.Column(
        db.String(100),
        nullable=True
    )

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    agent_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    customer = db.relationship(
        "User",
        foreign_keys=[customer_id],
        backref="customer_tickets"
    )

    agent = db.relationship(
        "User",
        foreign_keys=[agent_id],
        backref="assigned_tickets"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "category": self.category,
            "customer_id": self.customer_id,
            "agent_id": self.agent_id,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at
                else None
            ),
        }