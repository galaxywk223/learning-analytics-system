"""
后端API配置文件
"""

import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


def resolve_upload_folder(default_path: str) -> str:
    """Resolve upload folder from environment with sensible defaults."""
    env_path = os.environ.get("UPLOAD_FOLDER")
    if env_path:
        if not os.path.isabs(env_path):
            env_path = os.path.join(basedir, env_path)
        return os.path.abspath(env_path)
    return os.path.abspath(default_path)


def resolve_max_content_length(default_mb: int = 64) -> int:
    """
    Resolve Flask MAX_CONTENT_LENGTH from env.

    1) Use MAX_CONTENT_LENGTH (bytes) when explicitly provided.
    2) Otherwise read MAX_UPLOAD_SIZE_MB (megabytes, human friendly).
    3) Fallback to default when parsing fails.
    """
    raw_bytes = os.environ.get("MAX_CONTENT_LENGTH")
    if raw_bytes:
        try:
            value = int(raw_bytes)
            if value > 0:
                return value
        except ValueError:
            pass

    raw_mb = os.environ.get("MAX_UPLOAD_SIZE_MB")
    if raw_mb:
        try:
            mb_value = int(raw_mb)
            if mb_value > 0:
                return mb_value * 1024 * 1024
        except ValueError:
            pass

    return max(default_mb, 1) * 1024 * 1024


class Config:
    """基础配置"""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get(
        "GOOGLE_API_KEY"
    )
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    # AI健壮性配置
    AI_ENABLE_FALLBACK = os.environ.get("AI_ENABLE_FALLBACK", "1") not in {"0", "false", "False"}
    AI_MAX_RETRIES = int(os.environ.get("AI_MAX_RETRIES", "2"))
    AI_RETRY_BACKOFF = float(os.environ.get("AI_RETRY_BACKOFF", "1.25"))

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
    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:8080",
    ).split(",")
    CORS_SUPPORTS_CREDENTIALS = True

    # 上传配置
    UPLOAD_FOLDER = resolve_upload_folder(os.path.join(basedir, "uploads"))
    MAX_CONTENT_LENGTH = resolve_max_content_length()  # default 64MB, env overridable
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
    UPLOAD_FOLDER = resolve_upload_folder("/var/www/uploads")

    @staticmethod
    def init_app(app):
        Config.init_app(app)

        # 生产环境日志配置
        import logging
        from logging.handlers import RotatingFileHandler

        if not os.path.exists("logs"):
            os.mkdir("logs")

        file_handler = RotatingFileHandler(
            "logs/yinghuoji_api.log", maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info("萤火集 API startup")


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
