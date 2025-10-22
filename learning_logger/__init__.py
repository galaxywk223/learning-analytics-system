import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import config
import matplotlib
import jieba  # <-- 1. 导入 jieba
from flask import g, request, has_request_context

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

login_manager.login_view = "auth.login"
login_manager.login_message = "请先登录以访问此页面。"
login_manager.login_message_category = "info"


def create_app(config_name=os.getenv("FLASK_ENV", "default")):
    app = Flask(__name__, template_folder="../templates", static_folder="../static")

    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # === Logging & Monitoring ===
    import uuid
    from flask import g, request
    from pythonjsonlogger import jsonlogger

    # 1) 结构化日志（JSON） + 级别
    root_logger = logging.getLogger()
    # 清理可能的重复 handler（避免多次创建）
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        sh = logging.StreamHandler()
        fmt = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s"
        )
        sh.setFormatter(fmt)
        root_logger.addHandler(sh)
    root_logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

    # 2) 请求 ID 过滤器
    class RequestIdFilter(logging.Filter):
        def filter(self, record):
            # 仅在“有请求上下文”时读取 g/request；否则写入占位符
            if has_request_context():
                rid = request.headers.get("X-Request-ID") or getattr(
                    g, "request_id", "-"
                )
            else:
                rid = "-"
            record.request_id = rid
            return True

    for h in root_logger.handlers:
        h.addFilter(RequestIdFilter())

    @app.before_request
    def _inject_request_id():
        g.request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex)

    @app.after_request
    def _add_request_id_header(resp):
        rid = getattr(g, "request_id", None)
        if rid:
            resp.headers["X-Request-ID"] = rid
        return resp

    # 3) 可选 Sentry
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration

        SENTRY_DSN = os.getenv("SENTRY_DSN")
        if SENTRY_DSN:
            sentry_sdk.init(
                dsn=SENTRY_DSN,
                integrations=[FlaskIntegration()],
                traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
            )
            app.logger.info("Sentry initialized.")
    except Exception as e:
        app.logger.warning(f"Sentry init skipped: {e}")
    # === End Logging & Monitoring ===

    if app.config.get("SQLALCHEMY_ECHO"):
        sql_logger = logging.getLogger("sqlalchemy.engine")
        sql_logger.setLevel(logging.INFO)
        if not sql_logger.handlers:
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
            console_handler.setFormatter(formatter)
            sql_logger.addHandler(console_handler)
        print("=" * 50)
        print(
            "INFO: Logging for 'sqlalchemy.engine' has been programmatically enabled."
        )
        print("=" * 50)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    with app.app_context():
        from .blueprints.main import main_bp
        from .blueprints.records import records_bp
        from .blueprints.charts import charts_bp
        from .blueprints.countdown import countdown_bp
        from .blueprints.auth import auth_bp
        from .blueprints.todo import todo_bp
        from .blueprints.milestone import milestone_bp
        from .blueprints.daily_plan import daily_plan_bp
        from .blueprints.category_charts import category_charts_bp
        from .blueprints.stage import stage_bp
        from .blueprints.category import category_management_bp
        from .blueprints.motto_management import motto_management_bp

        app.register_blueprint(main_bp)
        app.register_blueprint(records_bp, url_prefix="/records")
        app.register_blueprint(charts_bp, url_prefix="/charts")
        app.register_blueprint(countdown_bp, url_prefix="/countdown")
        app.register_blueprint(auth_bp, url_prefix="/auth")
        app.register_blueprint(todo_bp)
        app.register_blueprint(milestone_bp, url_prefix="/milestones")
        app.register_blueprint(daily_plan_bp, url_prefix="/daily-plan")
        app.register_blueprint(category_charts_bp, url_prefix="/category_charts")
        app.register_blueprint(stage_bp)
        app.register_blueprint(category_management_bp)
        app.register_blueprint(motto_management_bp)

        from .models import User, Setting

        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

        @app.context_processor
        def inject_user_settings():
            if current_user.is_authenticated:
                settings_query = Setting.query.filter_by(user_id=current_user.id).all()
                user_settings = {
                    setting.key: setting.value for setting in settings_query
                }
                return dict(user_settings=user_settings)
            return dict(user_settings={})

        from . import helpers

        helpers.setup_template_filters(app)

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    # --- 2. 性能优化：在应用启动时预加载 jieba 词典 ---
    # 迁移/脚本等 CLI 场景可通过环境变量跳过重初始化
    if not os.getenv("SKIP_HEAVY_INIT"):
        app.logger.info("Initializing jieba dictionary...")
        jieba.initialize()
        app.logger.info("Jieba dictionary initialized successfully.")
    else:
        app.logger.info("Skipping jieba initialization due to SKIP_HEAVY_INIT=1")
    # --- 结束优化 ---

    return app
