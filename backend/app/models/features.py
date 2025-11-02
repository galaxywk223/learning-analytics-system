"""
应用功能模型
倒计时、座右铭、待办事项等功能相关的数据库模型
"""

from app import db
from datetime import datetime


class CountdownEvent(db.Model):
    """倒计时事件模型"""

    __tablename__ = "countdown_event"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    target_datetime_utc = db.Column(db.DateTime(timezone=True), nullable=False)
    created_at_utc = db.Column(
        db.DateTime(timezone=True), nullable=True, default=datetime.utcnow
    )
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "target_datetime_utc": self.target_datetime_utc.isoformat()
            if self.target_datetime_utc
            else None,
            "created_at_utc": self.created_at_utc.isoformat()
            if self.created_at_utc
            else None,
            "user_id": self.user_id,
        }

    def __repr__(self):
        return f"<CountdownEvent {self.title}>"


class Motto(db.Model):
    """座右铭模型"""

    __tablename__ = "motto"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Motto {self.content[:20]}>"


class Todo(db.Model):
    """待办事项模型"""

    __tablename__ = "todo"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    priority = db.Column(db.Integer, default=2)  # 1-高 2-中 3-低
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "priority": self.priority,
            "is_completed": self.is_completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "user_id": self.user_id,
        }

    def __repr__(self):
        return f"<Todo {self.content[:20]}>"
