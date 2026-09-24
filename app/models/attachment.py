from datetime import datetime, timezone

from app.extensions import db


class Attachment(db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True)

    ticket_id = db.Column(
        db.Integer,
        db.ForeignKey("tickets.id"),
        nullable=False,
    )

    uploaded_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )

    original_filename = db.Column(
        db.String(255),
        nullable=False,
    )

    stored_filename = db.Column(
        db.String(255),
        nullable=False,
        unique=True,
    )

    file_path = db.Column(
        db.String(500),
        nullable=False,
    )

    mime_type = db.Column(
        db.String(100),
        nullable=False,
    )

    file_size = db.Column(
        db.Integer,
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    ticket = db.relationship(
        "Ticket",
        backref=db.backref(
            "attachments",
            lazy=True,
            cascade="all, delete-orphan",
        ),
    )

    uploader = db.relationship(
        "User",
        backref=db.backref("attachments", lazy=True),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "uploaded_by": self.uploaded_by,
            "original_filename": self.original_filename,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat(),
        }