"""
里程碑模型
里程碑和相关附件的数据库模型
"""

from app import db
from datetime import date, datetime


class MilestoneCategory(db.Model):
    """里程碑分类模型"""

    __tablename__ = "milestone_category"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # 关系
    milestones = db.relationship(
        "Milestone", backref="category", lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {"id": self.id, "name": self.name, "user_id": self.user_id}

    def __repr__(self):
        return f"<MilestoneCategory {self.name}>"


class Milestone(db.Model):
    """里程碑模型"""

    __tablename__ = "milestone"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    event_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    description = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey("milestone_category.id"), nullable=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    attachments = db.relationship(
        "MilestoneAttachment",
        backref="milestone",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def to_dict(self, include_attachments=False):
        data = {
            "id": self.id,
            "title": self.title,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "description": self.description,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_attachments:
            data["attachments"] = [att.to_dict() for att in self.attachments]
        return data

    def __repr__(self):
        return f"<Milestone {self.title}>"


class MilestoneAttachment(db.Model):
    """里程碑附件模型"""

    __tablename__ = "milestone_attachment"

    id = db.Column(db.Integer, primary_key=True)
    milestone_id = db.Column(db.Integer, db.ForeignKey("milestone.id"), nullable=False)
    file_path = db.Column(db.String(256), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "milestone_id": self.milestone_id,
            "file_path": self.file_path,
            "original_filename": self.original_filename,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }

    def __repr__(self):
        return f"<MilestoneAttachment {self.original_filename}>"
