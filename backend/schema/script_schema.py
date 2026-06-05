from __future__ import annotations

from typing import Any

import yaml
from jsonschema import Draft202012Validator


ScriptDict = dict[str, Any]

SCRIPT_SCHEMA: ScriptDict = {
    "type": "object",
    "required": ["title", "acts", "characters"],
    "properties": {
        "title": {"type": "string"},
        "characters": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
        },
        "acts": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["number", "title", "scenes"],
                "properties": {
                    "number": {"type": "integer", "minimum": 1},
                    "title": {"type": "string"},
                    "scenes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["number", "title", "source_chapter", "beats"],
                            "properties": {
                                "number": {"type": "integer", "minimum": 1},
                                "title": {"type": "string"},
                                "source_chapter": {"type": "integer", "minimum": 1},
                                "summary": {"type": "string"},
                                "beats": {
                                    "type": "array",
                                    "minItems": 1,
                                    "items": {
                                        "type": "object",
                                        "required": ["type", "content"],
                                        "properties": {
                                            "type": {
                                                "type": "string",
                                                "enum": ["dialogue", "action", "direction"],
                                            },
                                            "character": {"type": "string"},
                                            "content": {"type": "string"},
                                            "parenthetical": {"type": "string"},
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    },
}


def build_script(
    title: str,
    chapters: list[dict[str, object]],
    characters: list[dict[str, str]],
    scenes: list[dict[str, object]] | None = None,
) -> ScriptDict:
    return {
        "title": title,
        "characters": characters,
        "acts": [
            {
                "number": 1,
                "title": "Act 1",
                "scenes": scenes if scenes is not None else [build_scene(chapter) for chapter in chapters],
            }
        ],
    }


def build_scene(chapter: dict[str, object]) -> dict[str, object]:
    excerpt = str(chapter.get("excerpt") or chapter.get("text") or "")
    beats = []
    for paragraph in [line.strip() for line in excerpt.split("\n") if line.strip()][:5]:
        if "\uff1a" in paragraph or ":" in paragraph:
            character, content = split_dialogue(paragraph)
            beats.append({"type": "dialogue", "character": character, "content": content})
        else:
            beats.append({"type": "action", "content": paragraph})

    if not beats:
        beats.append({"type": "direction", "content": "Scene pending completion."})

    return {
        "number": int(chapter["index"]),
        "title": str(chapter["title"]),
        "source_chapter": int(chapter["index"]),
        "summary": str(excerpt)[:120],
        "beats": beats,
    }


def split_dialogue(paragraph: str) -> tuple[str, str]:
    separator = "\uff1a" if "\uff1a" in paragraph else ":"
    character, content = paragraph.split(separator, 1)
    return character.strip()[:24] or "Character", content.strip()


def validate_script(script: ScriptDict) -> None:
    Draft202012Validator(SCRIPT_SCHEMA).validate(script)


def dump_script_yaml(script: ScriptDict) -> str:
    return yaml.safe_dump(script, allow_unicode=True, sort_keys=False)
