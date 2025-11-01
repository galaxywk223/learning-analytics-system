"""
Flask应用工厂
"""

import os
import logging
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import config
import matplotlib

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()


def create_app(config_name=None):
    """应用工厂函数"""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)

    # 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # 设置matplotlib后端
    matplotlib.use(app.config["MATPLOTLIB_BACKEND"])

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(
        app,
        origins=app.config["CORS_ORIGINS"],
        supports_credentials=app.config["CORS_SUPPORTS_CREDENTIALS"],
    )

    # 配置日志
    setup_logging(app)

    # 注册蓝图
    register_blueprints(app)

    # 注册错误处理
    register_error_handlers(app)

    # JWT回调函数
    register_jwt_callbacks(app)

    # 健康检查端点
    @app.route("/health")
    def health_check():
        return jsonify({"status": "healthy", "environment": config_name}), 200

    @app.route("/api")
    def api_root():
        return jsonify(
            {
                "message": "Learning Logger API",
                "version": "2.0.0",
                "endpoints": {
                    "auth": "/api/auth",
                    "users": "/api/users",
                    "stages": "/api/stages",
                    "categories": "/api/categories",
                    "records": "/api/records",
                    "charts": "/api/charts",
                    "todos": "/api/todos",
                    "milestones": "/api/milestones",
                    # "daily-plans": "/api/daily-plans",  # 屏蔽
                    "countdowns": "/api/countdowns",
                    # "mottos": "/api/mottos",  # 屏蔽
                },
            }
        ), 200

    return app


def setup_logging(app):
    """配置日志"""
    from pythonjsonlogger import jsonlogger

    root_logger = logging.getLogger()

    # 避免重复添加handler
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s"
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    root_logger.setLevel(app.config["LOG_LEVEL"])

    # Sentry集成(可选)
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration

            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[FlaskIntegration()],
                traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
            )
            app.logger.info("Sentry initialized")
        except Exception as e:
            app.logger.warning(f"Sentry initialization failed: {e}")


def register_blueprints(app):
    """注册所有蓝图"""
    from app.api import auth, users, stages, categories, records, charts
    from app.api import todos, milestones, countdowns, mottos

    # 注册API蓝图
    app.register_blueprint(auth.bp, url_prefix="/api/auth")
    app.register_blueprint(users.bp, url_prefix="/api/users")
    app.register_blueprint(stages.bp, url_prefix="/api/stages")
    app.register_blueprint(categories.bp, url_prefix="/api/categories")
    app.register_blueprint(records.bp, url_prefix="/api/records")
    app.register_blueprint(charts.bp, url_prefix="/api/charts")
    app.register_blueprint(todos.bp, url_prefix="/api/todos")
    app.register_blueprint(milestones.bp, url_prefix="/api/milestones")
    # app.register_blueprint(daily_plans.bp, url_prefix="/api/daily-plans")  # 屏蔽每日计划
    app.register_blueprint(countdowns.bp, url_prefix="/api/countdowns")
    app.register_blueprint(mottos.bp, url_prefix="/api/mottos")  # 恢复座右铭


def register_error_handlers(app):
    """注册错误处理器"""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify(
            {"success": False, "error": "Bad Request", "message": str(error)}
        ), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify(
            {
                "success": False,
                "error": "Unauthorized",
                "message": "Authentication required",
            }
        ), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify(
            {
                "success": False,
                "error": "Forbidden",
                "message": "You do not have permission to access this resource",
            }
        ), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify(
            {
                "success": False,
                "error": "Not Found",
                "message": "The requested resource was not found",
            }
        ), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal error: {error}")
        return jsonify(
            {
                "success": False,
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
            }
        ), 500


def register_jwt_callbacks(app):
    """注册JWT回调函数"""

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify(
            {
                "success": False,
                "error": "Token Expired",
                "message": "The token has expired",
            }
        ), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify(
            {
                "success": False,
                "error": "Invalid Token",
                "message": "Token validation failed",
            }
        ), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify(
            {
                "success": False,
                "error": "Authorization Required",
                "message": "Request does not contain an access token",
            }
        ), 401
