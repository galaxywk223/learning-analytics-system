"""
学习相关模型
学习阶段、分类和日志相关的数据库模型
"""

from app import db
from datetime import date, datetime


class Stage(db.Model):
    """学习阶段模型"""

    __tablename__ = "stage"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # 关系
    weekly_data = db.relationship(
        "WeeklyData", backref="stage", lazy="dynamic", cascade="all, delete-orphan"
    )
    daily_data = db.relationship(
        "DailyData", backref="stage", lazy="dynamic", cascade="all, delete-orphan"
    )
    log_entries = db.relationship(
        "LogEntry", backref="stage", lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "start_date": self.start_date.isoformat(),
            "user_id": self.user_id,
        }

    def __repr__(self):
        return f"<Stage {self.name}>"


class Category(db.Model):
    """分类模型"""

    __tablename__ = "category"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # 关系
    subcategories = db.relationship(
        "SubCategory", backref="category", lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_dict(self, include_subcategories=False):
        data = {"id": self.id, "name": self.name, "user_id": self.user_id}
        if include_subcategories:
            data["subcategories"] = [sub.to_dict() for sub in self.subcategories.all()]
        return data

    def __repr__(self):
        return f"<Category {self.name}>"


class SubCategory(db.Model):
    """子分类模型"""

    __tablename__ = "sub_category"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)

    # 关系
    log_entries = db.relationship("LogEntry", backref="subcategory", lazy="dynamic")

    def to_dict(self, include_category=False):
        data = {"id": self.id, "name": self.name, "category_id": self.category_id}
        if include_category and self.category:
            data["category"] = {
                "id": self.category.id,
                "name": self.category.name,
            }
        return data

    def __repr__(self):
        return f"<SubCategory {self.name}>"


class LogEntry(db.Model):
    """学习日志条目模型"""

    __tablename__ = "log_entry"

    id = db.Column(db.Integer, primary_key=True)
    log_date = db.Column(db.Date, nullable=False, index=True)
    time_slot = db.Column(db.String(50), nullable=True)
    task = db.Column(db.String(200), nullable=False)
    actual_duration = db.Column(db.Integer, nullable=True)  # 分钟
    legacy_category = db.Column(db.String(100), nullable=True)
    mood = db.Column(db.Integer, nullable=True)  # 1-5
    notes = db.Column(db.Text, nullable=True)
    stage_id = db.Column(db.Integer, db.ForeignKey("stage.id"), nullable=False)
    subcategory_id = db.Column(
        db.Integer, db.ForeignKey("sub_category.id"), nullable=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def duration_formatted(self):
        """格式化时长"""
        if self.actual_duration is None:
            return ""
        h, m = divmod(self.actual_duration, 60)
        return f"{h}h {m}m" if h > 0 else f"{m}m"

    def to_dict(self):
        result = {
            "id": self.id,
            "log_date": self.log_date.isoformat(),
            "time_slot": self.time_slot,
            "task": self.task,
            "actual_duration": self.actual_duration,
            "duration_formatted": self.duration_formatted,
            "legacy_category": self.legacy_category,
            "subcategory_id": self.subcategory_id,
            "mood": self.mood,
            "notes": self.notes,
            "stage_id": self.stage_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        # 包含子分类和分类信息
        if self.subcategory:
            result["subcategory"] = {
                "id": self.subcategory.id,
                "name": self.subcategory.name,
                "category_id": self.subcategory.category_id,
                "category": {
                    "id": self.subcategory.category.id,
                    "name": self.subcategory.category.name,
                }
                if self.subcategory.category
                else None,
            }
        else:
            result["subcategory"] = None
        return result

    def __repr__(self):
        return f"<LogEntry {self.task[:20]}>"
