import re

from django.conf import settings

from converter.models import ConversionTask
from converter.services.chapter_splitter import Chapter, split_chapters
from converter.services.llm_scene_converter import (
    ClaudeSceneConverter,
    OpenAICompatibleSceneConverter,
    SceneConverter,
)
from schema.script_schema import build_scene, build_script, dump_script_yaml, validate_script


SPEAKER_RE = re.compile(r"(?m)^([A-Za-z0-9_\u4e00-\u9fa5]{1,12})[\uff1a:]\s*(.+)$")


def run_conversion_task(task: ConversionTask) -> None:
    task.status = ConversionTask.Status.PROCESSING
    task.progress = 10
    task.save(update_fields=["status", "progress", "updated_at"])

    chapters = split_chapters(task.source_text)
    task.total_chapters = len(chapters)
    task.progress = 25
    task.save(update_fields=["total_chapters", "progress", "updated_at"])

    characters = extract_character_table(task.source_text)
    chapter_payloads = [chapter_to_payload(chapter) for chapter in chapters]
    scene_converter = build_scene_converter()
    scenes = []

    for chapter in chapters:
        scenes.append(scene_converter.convert_chapter(chapter, characters))
        task.chapters_done = len(scenes)
        task.progress = conversion_progress(len(scenes), len(chapters))
        task.save(update_fields=["chapters_done", "progress", "updated_at"])

    script = build_script(
        title=task.input_name or "Untitled",
        chapters=chapter_payloads,
        characters=characters,
        scenes=scenes,
    )
    validate_script(script)

    task.characters = characters
    task.chapters = chapter_payloads
    task.script_yaml = dump_script_yaml(script)
    task.chapters_done = len(chapters)
    task.progress = 100
    task.status = ConversionTask.Status.COMPLETED
    task.save(
        update_fields=[
            "characters",
            "chapters",
            "script_yaml",
            "chapters_done",
            "progress",
            "status",
            "updated_at",
        ]
    )


class PlaceholderSceneConverter:
    def convert_chapter(
        self,
        chapter: Chapter,
        characters: list[dict[str, str]],  # noqa: ARG002
    ) -> dict[str, object]:
        return build_scene(chapter_to_payload(chapter))


def build_scene_converter() -> SceneConverter:
    provider = resolve_llm_provider()
    if provider == "placeholder":
        return PlaceholderSceneConverter()

    if provider == "anthropic":
        return ClaudeSceneConverter(
            api_key=settings.ANTHROPIC_API_KEY.strip(),
            model=settings.ANTHROPIC_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
        )

    if provider == "openai":
        return OpenAICompatibleSceneConverter(
            provider_name="openai",
            api_key=settings.OPENAI_API_KEY.strip(),
            base_url=settings.OPENAI_BASE_URL,
            model=settings.OPENAI_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            json_mode=settings.OPENAI_JSON_MODE,
        )

    if provider == "qwen":
        return OpenAICompatibleSceneConverter(
            provider_name="qwen",
            api_key=settings.QWEN_API_KEY.strip(),
            base_url=settings.QWEN_BASE_URL,
            model=settings.QWEN_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            json_mode=settings.QWEN_JSON_MODE,
        )

    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


def resolve_llm_provider() -> str:
    provider = settings.LLM_PROVIDER.strip().lower()
    supported_providers = {"auto", "placeholder", "anthropic", "openai", "qwen"}
    if provider not in supported_providers:
        raise ValueError(f"LLM_PROVIDER must be one of: {', '.join(sorted(supported_providers))}")

    if provider == "placeholder":
        return "placeholder"

    provider_keys = {
        "anthropic": settings.ANTHROPIC_API_KEY.strip(),
        "openai": settings.OPENAI_API_KEY.strip(),
        "qwen": settings.QWEN_API_KEY.strip(),
    }
    if provider == "auto":
        for candidate in ("anthropic", "openai", "qwen"):
            if provider_keys[candidate]:
                return candidate
        return "placeholder"

    if not provider_keys[provider]:
        raise ValueError(f"LLM_PROVIDER={provider} requires its API key to be configured.")
    return provider


def conversion_progress(chapters_done: int, total_chapters: int) -> int:
    if total_chapters <= 0:
        return 90
    return min(95, 25 + int((chapters_done / total_chapters) * 65))


def extract_character_table(text: str) -> list[dict[str, str]]:
    names = []
    seen: set[str] = set()
    for match in SPEAKER_RE.finditer(text):
        name = match.group(1).strip()
        if name not in seen:
            seen.add(name)
            names.append(
                {
                    "name": name,
                    "role": "\u5f85\u5b9a",
                    "description": "\u4ece\u539f\u6587\u5bf9\u8bdd\u4e2d\u8bc6\u522b",
                }
            )
        if len(names) >= 12:
            break
    return names


def chapter_to_payload(chapter: Chapter) -> dict[str, object]:
    paragraphs = [paragraph for paragraph in chapter.text.split("\n") if paragraph.strip()]
    return {
        "index": chapter.index,
        "title": chapter.title,
        "text": chapter.text,
        "excerpt": "\n".join(paragraphs[:3])[:500],
    }
