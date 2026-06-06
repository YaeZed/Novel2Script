from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.conf import settings

from converter.services.chapter_splitter import Chapter
from converter.services.error_messages import is_auth_error
from converter.services.llm_scene_converter import SceneConverter


@dataclass(frozen=True)
class ChapterConversionResult:
    scene: dict[str, object]
    manual_review_label: str = ""


def convert_chapter_with_retry(
    converter: SceneConverter,
    chapter: Chapter,
    characters: list[dict[str, str]],
) -> ChapterConversionResult:
    max_attempts = max(1, int(getattr(settings, "LLM_SCENE_MAX_ATTEMPTS", 2)))

    for _attempt in range(1, max_attempts + 1):
        try:
            return ChapterConversionResult(scene=converter.convert_chapter(chapter, characters))
        except Exception as exc:  # noqa: BLE001
            if is_non_recoverable_conversion_error(exc):
                raise

    return ChapterConversionResult(
        scene=build_manual_review_scene(chapter, attempts=max_attempts),
        manual_review_label=chapter_label(chapter),
    )


def is_non_recoverable_conversion_error(exc: Exception) -> bool:
    lowered = f"{exc.__class__.__name__}: {exc}".lower()
    if is_auth_error(lowered):
        return True
    return (
        ("llm_provider" in lowered and "requires its api key" in lowered)
        or "llm_provider must be one of" in lowered
        or "unsupported llm_provider" in lowered
    )


def build_manual_review_scene(
    chapter: Chapter,
    *,
    attempts: int,
) -> dict[str, object]:
    summary = f"本章模型转换连续 {attempts} 次未得到可用 Scene，已标记为人工处理。"
    beats: list[dict[str, str]] = [
        {
            "type": "direction",
            "content": f"{summary}请参考左侧原文重写本场。",
        }
    ]
    if excerpt := source_excerpt(chapter.text):
        beats.append({"type": "action", "content": f"原文摘录：{excerpt}"})

    return {
        "number": chapter.index,
        "title": f"{chapter.title}（需人工处理）",
        "source_chapter": chapter.index,
        "summary": summary,
        "beats": beats,
    }


def build_manual_review_message(labels: list[str]) -> str:
    if not labels:
        return ""

    joined = "、".join(labels[:5])
    if len(labels) > 5:
        joined = f"{joined} 等 {len(labels)} 章"
    return f"{joined} 转换失败，已生成需人工处理的占位场。可打开对照页按标记场景修正。"


def chapter_label(chapter: Chapter) -> str:
    title = trim_text(chapter.title, 28)
    return f"第 {chapter.index} 章《{title}》"


def source_excerpt(text: str) -> str:
    paragraphs = [line.strip() for line in text.splitlines() if line.strip()]
    return trim_text(" ".join(paragraphs[:3]), 420)


def trim_text(value: Any, limit: int) -> str:
    text = str(value).strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}..."
