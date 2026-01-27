import sys
from pathlib import Path
from datetime import date

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import create_app, db
from app.models import User, Stage, Category, SubCategory, LogEntry
from app.services import record_service


def main():
    app = create_app("testing")
    with app.app_context():
        db.create_all()

        user = User(username="verify", email="verify@test.com")
        user.set_password("pw123")
        db.session.add(user)
        db.session.flush()

        stage_fall = Stage(name="大三上学期", start_date=date(2025, 9, 1), user_id=user.id)
        stage_winter = Stage(name="大三寒假", start_date=date(2026, 1, 13), user_id=user.id)
        db.session.add_all([stage_fall, stage_winter])
        db.session.flush()

        category = Category(name="分类", user_id=user.id)
        db.session.add(category)
        db.session.flush()
        sub = SubCategory(name="子类", category_id=category.id)
        db.session.add(sub)
        db.session.flush()

        wrong = LogEntry(
            log_date=date(2026, 1, 27),
            task="should be winter",
            actual_duration=30,
            stage_id=stage_fall.id,
            subcategory_id=sub.id,
        )
        ok = LogEntry(
            log_date=date(2026, 1, 10),
            task="should be fall",
            actual_duration=30,
            stage_id=stage_fall.id,
            subcategory_id=sub.id,
        )
        db.session.add_all([wrong, ok])
        db.session.commit()

        fall_structured = record_service.get_structured_logs_for_stage(stage_fall, "asc")
        winter_structured = record_service.get_structured_logs_for_stage(stage_winter, "asc")

        fall_dates = sorted(
            {day["date"] for week in fall_structured for day in week["days"]}
        )
        winter_dates = sorted(
            {day["date"] for week in winter_structured for day in week["days"]}
        )

        print("fall_dates", [d.isoformat() for d in fall_dates])
        print("winter_dates", [d.isoformat() for d in winter_dates])

        assert date(2026, 1, 27) not in fall_dates
        assert date(2026, 1, 27) in winter_dates

        refreshed = LogEntry.query.filter_by(id=wrong.id).first()
        assert refreshed.stage_id == stage_winter.id


if __name__ == "__main__":
    main()
