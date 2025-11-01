"""
数据库模型
"""

from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime


class User(db.Model):
    """用户模型"""

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    stages = db.relationship(
        "Stage", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    categories = db.relationship(
        "Category", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    milestone_categories = db.relationship(
        "MilestoneCategory",
        backref="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    milestones = db.relationship(
        "Milestone", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    countdown_events = db.relationship(
        "CountdownEvent", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    settings = db.relationship(
        "Setting", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    mottos = db.relationship(
        "Motto", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    todos = db.relationship(
        "Todo", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    daily_plans = db.relationship(
        "DailyPlanItem", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User {self.username}>"


class Setting(db.Model):
    """用户设置模型"""

    __tablename__ = "setting"

    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(200), nullable=False)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, primary_key=True
    )

    def to_dict(self):
        return {"key": self.key, "value": self.value}


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


class WeeklyData(db.Model):
    """周统计数据模型"""

    __tablename__ = "weekly_data"

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    week_num = db.Column(db.Integer, nullable=False)
    efficiency = db.Column(db.Float, nullable=True)
    stage_id = db.Column(db.Integer, db.ForeignKey("stage.id"), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("year", "week_num", "stage_id", name="_stage_year_week_uc"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "year": self.year,
            "week_num": self.week_num,
            "efficiency": self.efficiency,
            "stage_id": self.stage_id,
        }


class DailyData(db.Model):
    """日统计数据模型"""

    __tablename__ = "daily_data"

    id = db.Column(db.Integer, primary_key=True)
    log_date = db.Column(db.Date, nullable=False, index=True)
    efficiency = db.Column(db.Float, nullable=True)
    stage_id = db.Column(db.Integer, db.ForeignKey("stage.id"), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("log_date", "stage_id", name="_stage_log_date_uc"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "log_date": self.log_date.isoformat(),
            "efficiency": self.efficiency,
            "stage_id": self.stage_id,
        }


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
