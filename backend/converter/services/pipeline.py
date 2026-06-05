import re

from converter.models import ConversionTask
from converter.services.chapter_splitter import Chapter, split_chapters
from schema.script_schema import build_script, dump_script_yaml, validate_script


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
    script = build_script(
        title=task.input_name or "Untitled",
        chapters=chapter_payloads,
        characters=characters,
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
