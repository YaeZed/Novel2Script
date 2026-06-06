from django.conf import settings

from converter.models import ConversionTask
from converter.services.character_extractor import extract_character_table
from converter.services.chapter_splitter import Chapter, split_chapters
from converter.services.llm_scene_converter import (
    ClaudeSceneConverter,
    OpenAICompatibleSceneConverter,
    SceneConverter,
)
from converter.services.conversion_recovery import (
    build_manual_review_message,
    convert_chapter_with_retry,
)
from converter.services.script_assembler import assemble_script
from schema.script_schema import build_scene, dump_script_yaml, validate_script


def run_conversion_task(task: ConversionTask) -> None:
    task.status = ConversionTask.Status.PROCESSING
    task.progress = 10
    task.save(update_fields=["status", "progress", "updated_at"])

    chapters = split_chapters(task.source_text)
    chapter_payloads = [chapter_to_payload(chapter) for chapter in chapters]
    task.total_chapters = len(chapters)
    task.chapters = chapter_payloads
    task.progress = 25
    task.save(update_fields=["total_chapters", "chapters", "progress", "updated_at"])

    characters = extract_character_table(task.source_text)
    scene_converter = build_scene_converter()
    scenes = []
    manual_review_labels = []

    for chapter in chapters:
        conversion = convert_chapter_with_retry(scene_converter, chapter, characters)
        scenes.append(conversion.scene)
        if conversion.manual_review_label:
            manual_review_labels.append(conversion.manual_review_label)
        task.chapters_done = len(scenes)
        task.progress = conversion_progress(len(scenes), len(chapters))
        task.save(update_fields=["chapters_done", "progress", "updated_at"])

    script = assemble_script(
        title=task.input_name or "Untitled",
        characters=characters,
        scenes=scenes,
    )
    validate_script(script)

    task.characters = characters
    task.chapters = chapter_payloads
    task.script_yaml = dump_script_yaml(script)
    task.error_message = build_manual_review_message(manual_review_labels)
    task.chapters_done = len(chapters)
    task.progress = 100
    task.status = ConversionTask.Status.COMPLETED
    task.save(
        update_fields=[
            "characters",
            "chapters",
            "script_yaml",
            "error_message",
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
        characters: list[dict[str, str]],
    ) -> dict[str, object]:
        return build_scene(chapter_to_payload(chapter), characters=characters)


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


def chapter_to_payload(chapter: Chapter) -> dict[str, object]:
    paragraphs = [paragraph for paragraph in chapter.text.split("\n") if paragraph.strip()]
    return {
        "index": chapter.index,
        "title": chapter.title,
        "text": chapter.text,
        "excerpt": "\n".join(paragraphs[:3])[:500],
    }
