"""
数据分析模型
学习数据统计和分析相关的数据库模型
"""

from app import db


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
