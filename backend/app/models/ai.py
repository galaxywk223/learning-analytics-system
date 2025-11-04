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
        return {
            "id": self.id,
            "user_id": self.user_id,
            "insight_type": self.insight_type,
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
            "input_snapshot": self.input_snapshot,
            "output_text": self.output_text,
        }
