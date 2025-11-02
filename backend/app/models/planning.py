"""
日程计划模型
每日计划相关的数据库模型
"""

from app import db
from datetime import date, datetime


class DailyPlanItem(db.Model):
    """每日计划项模型"""

    __tablename__ = "daily_plan_item"

    id = db.Column(db.Integer, primary_key=True)
    plan_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    content = db.Column(db.String(500), nullable=False)
    time_slot = db.Column(db.String(20), nullable=True)
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "plan_date": self.plan_date.isoformat() if self.plan_date else None,
            "content": self.content,
            "time_slot": self.time_slot,
            "is_completed": self.is_completed,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<DailyPlanItem {self.content[:30]}>"
