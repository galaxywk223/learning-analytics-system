"""
后端API配置文件
"""

import os
import re
from typing import Final
from datetime import timedelta
from urllib.parse import quote, unquote_to_bytes, urlsplit, urlunsplit

basedir = os.path.abspath(os.path.dirname(__file__))
PERCENT_ENCODED_RUN_RE = re.compile(r"(?:%[0-9A-Fa-f]{2})+")


def normalize_postgres_url(raw_url: str | None) -> str | None:
    """
    Normalize PostgreSQL URL userinfo to avoid decode failures in psycopg2.

    This primarily handles credentials that were percent-encoded with a
    non-UTF-8 charset (common on Windows shells), e.g. `%D6%D0`.
    """
    if not raw_url:
        return raw_url

    normalized_url = raw_url.strip()
    if (
        len(normalized_url) >= 2
        and normalized_url[0] == normalized_url[-1]
        and normalized_url[0] in {"'", '"'}
    ):
        normalized_url = normalized_url[1:-1].strip()

    if not normalized_url:
        return normalized_url

    scheme = urlsplit(normalized_url).scheme.lower()
    if not (scheme.startswith("postgresql") or scheme == "postgres"):
        return raw_url

    fallback_encodings: Final[tuple[str, ...]] = ("utf-8", "gb18030", "gbk", "latin-1")

    def _repair_percent_encoded_runs(text: str) -> str:
        def _replace(match: re.Match[str]) -> str:
            chunk = match.group(0)
            raw_bytes = unquote_to_bytes(chunk)
            try:
                raw_bytes.decode("utf-8")
                return chunk
            except UnicodeDecodeError:
                for encoding in fallback_encodings:
                    try:
                        decoded = raw_bytes.decode(encoding)
                        return quote(decoded, safe="")
                    except UnicodeDecodeError:
                        continue
                return chunk

        return PERCENT_ENCODED_RUN_RE.sub(_replace, text)

    # First pass: repair broken percent-encoded bytes globally.
    normalized_url = _repair_percent_encoded_runs(normalized_url)

    parsed = urlsplit(normalized_url)

    def _normalize_component(component: str, safe: str = "") -> str:
        if not component:
            return component
        if "%" in component:
            raw_bytes = unquote_to_bytes(component)
            try:
                raw_bytes.decode("utf-8")
                return component
            except UnicodeDecodeError:
                for encoding in fallback_encodings:
                    try:
                        decoded = raw_bytes.decode(encoding)
                        return quote(decoded, safe=safe)
                    except UnicodeDecodeError:
                        continue
                return component
        return quote(component, safe=safe)

    normalized_netloc = parsed.netloc
    if "@" in parsed.netloc:
        userinfo, hostinfo = parsed.netloc.rsplit("@", 1)
        if ":" in userinfo:
            username, password = userinfo.split(":", 1)
        else:
            username, password = userinfo, None

        normalized_username = _normalize_component(username)
        normalized_userinfo = normalized_username
        if password is not None:
            normalized_password = _normalize_component(password)
            normalized_userinfo = f"{normalized_username}:{normalized_password}"
        normalized_netloc = f"{normalized_userinfo}@{hostinfo}"

    normalized_path = _normalize_component(parsed.path, safe="/")
    normalized_query = _normalize_component(parsed.query, safe="=&")
    normalized_fragment = _normalize_component(parsed.fragment)
    return urlunsplit(
        (
            parsed.scheme,
            normalized_netloc,
            normalized_path,
            normalized_query,
            normalized_fragment,
        )
    )


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

    QWEN_API_KEY = os.environ.get("QWEN_API_KEY") or os.environ.get(
        "DASHSCOPE_API_KEY"
    )
    QWEN_MODEL = os.environ.get("QWEN_MODEL", "qwen-plus-2025-07-28")
    QWEN_BASE_URL = os.environ.get(
        "QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
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
    SQLALCHEMY_DATABASE_URI = normalize_postgres_url(
        os.environ.get("DEV_DATABASE_URL")
    ) or "postgresql://postgres:123456@localhost:5432/learning_analytics_system"

    @staticmethod
    def init_app(app):
        Config.init_app(app)
        instance_path = os.path.join(basedir, "instance")
        os.makedirs(instance_path, exist_ok=True)


class ProductionConfig(Config):
    """生产环境配置"""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = normalize_postgres_url(
        os.environ.get("DATABASE_URL")
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
