from __future__ import annotations

from typing import Any, Dict
import time

from flask import current_app

try:
    from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError
except ImportError:  # pragma: no cover - handled at runtime
    OpenAI = None  # type: ignore[assignment]
    APIConnectionError = APIStatusError = RateLimitError = Exception  # type: ignore[assignment]

from .errors import AIPlannerError

# Cache a single client per API key/base_url to avoid re-instantiating the SDK on every call.
_qwen_client_cache: Dict[str, Any] = {}


def _configure_qwen():
    if OpenAI is None:
        raise AIPlannerError(
            "未安装 openai SDK，请先 pip install openai 或运行 pip install -r requirements.txt 安装依赖"
        )
    api_key = current_app.config.get("QWEN_API_KEY")
    if not api_key:
        raise AIPlannerError("未配置 Qwen API 密钥")
    base_url = current_app.config.get(
        "QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    cache_key = f"{api_key}@{base_url}"
    client = _qwen_client_cache.get(cache_key)
    if client is None:
        client = OpenAI(api_key=api_key, base_url=base_url)
        _qwen_client_cache.clear()
        _qwen_client_cache[cache_key] = client
    model_name = current_app.config.get("QWEN_MODEL", "qwen-plus-2025-07-28")
    return client, model_name


def _call_qwen(prompt: str) -> str:
    client, model_name = _configure_qwen()
    max_retries = int(current_app.config.get("AI_MAX_RETRIES", 2) or 0)
    backoff = float(current_app.config.get("AI_RETRY_BACKOFF", 1.25) or 1.25)
    attempt = 0
    last_error: Exception | None = None
    while attempt <= max_retries:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            if not response or not getattr(response, "choices", None):
                raise AIPlannerError("未能生成有效的模型输出")
            message = response.choices[0].message.content if response.choices else None
            if not message:
                raise AIPlannerError("模型未返回内容，请稍后重试")
            return str(message).strip()
        except (APIStatusError, RateLimitError) as exc:
            last_error = exc
            detail = getattr(exc, "message", None) or getattr(exc, "response", None) or str(exc)
            # 对临时性错误做重试
            transient = any(
                key in str(detail).lower()
                for key in [
                    "timeout",
                    "temporarily",
                    "unavailable",
                    "deadline",
                    "internal",
                    "quota",
                    "network",
                    "503",
                ]
            )
            if attempt < max_retries and transient:
                time.sleep(max(0.2, 0.6 * (backoff ** attempt)))
                attempt += 1
                continue
            raise AIPlannerError(
                f"调用通义千问接口失败：{detail}（模型：{model_name}）"
            ) from exc
        except APIConnectionError as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(max(0.2, 0.6 * (backoff ** attempt)))
                attempt += 1
                continue
            raise AIPlannerError("连接通义千问失败，请检查网络后重试") from exc
        except Exception as exc:
            last_error = exc
            # 常见 SSL/连接错误
            msg = str(exc)
            if attempt < max_retries and any(
                s in msg for s in [
                    "SSL:",
                    "EOF occurred",
                    "Connection reset",
                    "Connection aborted",
                    "RemoteDisconnected",
                ]
            ):
                time.sleep(max(0.2, 0.6 * (backoff ** attempt)))
                attempt += 1
                continue
            raise AIPlannerError(f"生成内容失败，请稍后重试：{exc}") from exc

    # 理论上到不了这里
    if last_error:
        raise AIPlannerError(f"生成内容失败，请稍后重试：{last_error}")
    raise AIPlannerError("生成内容失败：未知原因")


__all__ = ["_configure_qwen", "_call_qwen", "_qwen_client_cache"]
