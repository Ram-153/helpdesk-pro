from datetime import datetime, timezone

from app.extensions import db


class TicketComment(db.Model):
    __tablename__ = "ticket_comments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    ticket_id = db.Column(
        db.Integer,
        db.ForeignKey("tickets.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    ticket = db.relationship(
        "Ticket",
        backref="comments"
    )

    user = db.relationship(
        "User",
        backref="ticket_comments"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "user_id": self.user_id,
            "message": self.message,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            )
        }

