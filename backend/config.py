"""
后端API配置文件
"""

import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """基础配置"""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    # 数据库配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # JWT配置
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # CORS配置
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
    CORS_SUPPORTS_CREDENTIALS = True

    # 上传配置
    UPLOAD_FOLDER = os.path.join(basedir, "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    # Matplotlib后端
    MATPLOTLIB_BACKEND = "Agg"

    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


class DevelopmentConfig(Config):
    """开发环境配置"""

    DEBUG = True
    SQLALCHEMY_ECHO = True
    # PostgreSQL 配置
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DEV_DATABASE_URL")
        or "postgresql://postgres:wangkai0906@localhost:5432/learning-analytics-system"
    )

    @staticmethod
    def init_app(app):
        Config.init_app(app)
        instance_path = os.path.join(basedir, "instance")
        os.makedirs(instance_path, exist_ok=True)


class ProductionConfig(Config):
    """生产环境配置"""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "instance", "prod.db")

    # 生产环境上传目录
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or "/var/www/uploads"

    @staticmethod
    def init_app(app):
        Config.init_app(app)

        # 生产环境日志配置
        import logging
        from logging.handlers import RotatingFileHandler

        if not os.path.exists("logs"):
            os.mkdir("logs")

        file_handler = RotatingFileHandler(
            "logs/learning_logger_api.log", maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info("Learning Logger API startup")


class TestingConfig(Config):
    """测试环境配置"""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
