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
            f"{provider} 连接凭据无效或未授权。请让管理员检查对应的服务设置，"
            "修正后重启处理服务；如果只是本地演示，可先切回本地演示方式。"
        )

    if "llm_provider" in lowered and "requires its api key" in lowered:
        return (
            "当前选择的在线智能服务还没有配置连接凭据。请让管理员补齐设置，"
            "或先切回本地演示方式后重启处理服务。"
        )

    if "llm_provider must be one of" in lowered or "unsupported llm_provider" in lowered:
        return "当前选择的处理方式暂不支持。请让管理员改成可用的处理方式后重试。"

    if "response was not valid json" in lowered or "scene must include at least one beat" in lowered:
        return "生成结果的结构不完整。请重试；如果持续失败，可先切回本地演示方式检查主流程。"

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
    }.get(configured_provider, "在线智能服务")


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
