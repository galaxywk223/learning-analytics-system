"""
AI related models.
"""

from datetime import datetime

from app import db


class AIInsight(db.Model):
    """
    Stores AI generated analysis or planning results for a user.
    """

    __tablename__ = "ai_insight"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    insight_type = db.Column(db.String(20), nullable=False)  # analysis / plan
    scope = db.Column(db.String(20), nullable=False)  # day / week / month / stage
    scope_reference = db.Column(db.Integer, nullable=True)  # e.g. stage_id
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    next_start_date = db.Column(db.Date, nullable=True)
    next_end_date = db.Column(db.Date, nullable=True)
    input_snapshot = db.Column(db.JSON, nullable=True)
    output_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("ai_insights", lazy="dynamic"))

    def to_dict(self):
        snapshot = self.input_snapshot or {}
        return {
            "id": self.id,
            "user_id": self.user_id,
            "insight_type": self.insight_type,
            "workflow_type": snapshot.get("workflow_type", self.insight_type),
            "scope": self.scope,
            "scope_reference": self.scope_reference,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "next_start_date": self.next_start_date.isoformat()
            if self.next_start_date
            else None,
            "next_end_date": self.next_end_date.isoformat()
            if self.next_end_date
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "input_snapshot": snapshot,
            "output_text": self.output_text,
            "status_level": snapshot.get("status_level"),
            "core_judgement": snapshot.get("core_judgement"),
            "period_label": snapshot.get("period_label"),
            "next_period_label": snapshot.get("next_period_label"),
            "generation_mode": snapshot.get("meta", {}).get("generation_mode")
            or snapshot.get("generation_mode"),
            "generation_label": snapshot.get("meta", {}).get("generation_label")
            or snapshot.get("generation_label"),
        }


class AIChatSession(db.Model):
    """Visible AI chat sessions."""

    __tablename__ = "ai_chat_session"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False, default="新对话")
    scope = db.Column(db.String(20), nullable=False, default="week")
    scope_reference = db.Column(db.Integer, nullable=True)
    date_reference = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    last_message_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("ai_chat_sessions", lazy="dynamic"))
    messages = db.relationship(
        "AIChatMessage",
        backref="session",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="AIChatMessage.created_at.asc()",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "scope": self.scope,
            "scope_reference": self.scope_reference,
            "date_reference": self.date_reference.isoformat()
            if self.date_reference
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_message_at": self.last_message_at.isoformat()
            if self.last_message_at
            else None,
        }


class AIChatMessage(db.Model):
    """Visible AI chat messages only."""

    __tablename__ = "ai_chat_message"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer,
        db.ForeignKey("ai_chat_session.id"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    scope = db.Column(db.String(20), nullable=False, default="week")
    scope_reference = db.Column(db.Integer, nullable=True)
    date_reference = db.Column(db.Date, nullable=True)
    generation_mode = db.Column(db.String(30), nullable=True)
    model_name = db.Column(db.String(120), nullable=True)
    meta_snapshot = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("ai_chat_messages", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "role": self.role,
            "content": self.content,
            "scope": self.scope,
            "scope_reference": self.scope_reference,
            "date_reference": self.date_reference.isoformat()
            if self.date_reference
            else None,
            "generation_mode": self.generation_mode,
            "model_name": self.model_name,
            "meta": self.meta_snapshot or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
