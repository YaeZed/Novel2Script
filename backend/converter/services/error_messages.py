from __future__ import annotations

import re

from django.conf import settings


SECRET_RE = re.compile(r"(sk[-_][A-Za-z0-9]{3})[A-Za-z0-9_\-*.]{8,}([A-Za-z0-9]{3})")


def format_conversion_error(exc: Exception) -> str:
    raw_message = str(exc)
    lowered = raw_message.lower()
    provider = infer_provider(lowered)

    if is_auth_error(lowered):
        return (
            f"{provider} API key 无效或未授权。请检查 `backend/.env` 里的对应 key，"
            "修正后重启后端；如果只是本地演示，把 `LLM_PROVIDER=placeholder` 后重启。"
        )

    if "llm_provider" in lowered and "requires its api key" in lowered:
        return (
            "当前 `LLM_PROVIDER` 指向了未配置 key 的厂商。请补齐对应 API key，"
            "或改为 `LLM_PROVIDER=placeholder` 后重启后端。"
        )

    if "llm_provider must be one of" in lowered or "unsupported llm_provider" in lowered:
        return "LLM_PROVIDER 配置不支持。请使用 `auto`、`anthropic`、`openai`、`qwen` 或 `placeholder`。"

    if "response was not valid json" in lowered or "scene must include at least one beat" in lowered:
        return "模型返回的剧本结构不符合要求。请重试；如果持续失败，先切到 `LLM_PROVIDER=placeholder` 验证主流程。"

    return f"转换失败：{mask_secrets(raw_message)[:500]}"


def infer_provider(lowered_message: str) -> str:
    if "openai" in lowered_message or "platform.openai.com" in lowered_message:
        return "OpenAI"
    if "dashscope" in lowered_message or "qwen" in lowered_message or "aliyun" in lowered_message:
        return "阿里千问"
    if "anthropic" in lowered_message or "claude" in lowered_message or "x-api-key" in lowered_message:
        return "Anthropic"

    configured_provider = settings.LLM_PROVIDER.strip().lower()
    return {
        "anthropic": "Anthropic",
        "openai": "OpenAI",
        "qwen": "阿里千问",
    }.get(configured_provider, "LLM")


def is_auth_error(lowered_message: str) -> bool:
    if "authenticationerror" in lowered_message:
        return True

    auth_markers = [
        "incorrect api key",
        "invalid_api_key",
        "invalid api key",
        "authentication",
        "unauthorized",
        "401",
    ]
    secret_markers = ["api key", "token", "unauthorized", "401"]
    return any(marker in lowered_message for marker in auth_markers) and any(
        marker in lowered_message for marker in secret_markers
    )


def mask_secrets(message: str) -> str:
    return SECRET_RE.sub(r"\1...\2", message)
