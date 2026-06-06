from __future__ import annotations

import re
from typing import Any

import yaml
from jsonschema import Draft202012Validator


ScriptDict = dict[str, Any]
LABEL_RE = re.compile(
    r"(?:^|[\s\uff0c,\u3002\uff1b;\u3001])"
    r"(?P<name>[A-Za-z][A-Za-z0-9_ .'-]{0,31}|[\u4e00-\u9fff]{1,8})"
    r"[\uff1a:]"
)
CHINESE_ATTRIBUTED_DIALOGUE_RE = re.compile(
    r"[\u201c\u300c\u300e](?P<content>[^\u201d\u300d\u300f\n]{1,120})[\u201d\u300d\u300f]"
    r"[\uff0c,]?\s*(?P<name>[\u4e00-\u9fff]{2,4}?)"
    r"(?P<parenthetical>\u4f4e\u58f0|\u8f7b\u58f0|\u6c89\u58f0|\u5ffd\u7136)?"
    r"(?:\u8bf4|\u95ee|\u9053|\u558a|\u53eb|\u7b54|\u56de\u7b54|\u7b11\u9053)"
)
METADATA_LABELS = {
    "chapter",
    "scene",
    "title",
    "time",
    "place",
    "location",
    "note",
    "notes",
    "author",
    "\u7ae0\u8282",
    "\u6807\u9898",
    "\u65f6\u95f4",
    "\u5730\u70b9",
    "\u573a\u666f",
    "\u89d2\u8272",
    "\u4eba\u7269",
    "\u5929\u6c14",
    "\u9053\u5177",
    "\u5907\u6ce8",
    "\u8bf4\u660e",
    "\u4f5c\u8005",
    "\u76ee\u5f55",
}
GENERIC_NAMES = {
    "\u6211",
    "\u4f60",
    "\u4ed6",
    "\u5979",
    "\u5b83",
    "\u6211\u4eec",
    "\u4f60\u4eec",
    "\u4ed6\u4eec",
    "\u5979\u4eec",
    "\u90a3\u4eba",
    "\u6709\u4eba",
    "\u4f17\u4eba",
    "\u5927\u5bb6",
}

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
    scene_payloads = scenes if scenes is not None else [build_scene(chapter) for chapter in chapters]
    return {
        "title": title,
        "characters": characters,
        "acts": [
            {
                "number": 1,
                "title": "\u7b2c\u4e00\u5e55\uff1a\u5168\u7bc7",
                "scenes": scene_payloads,
            }
        ],
    }


def build_scene(
    chapter: dict[str, object],
    characters: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    excerpt = str(chapter.get("excerpt") or chapter.get("text") or "")
    known_names = {character["name"] for character in characters or [] if character.get("name")}
    beats = []
    for paragraph in [line.strip() for line in excerpt.split("\n") if line.strip()][:5]:
        multi_label_beats = build_multi_label_beats(paragraph, known_names)
        if multi_label_beats:
            beats.extend(multi_label_beats)
        elif attributed_dialogue := parse_attributed_dialogue(paragraph, known_names):
            beats.append(attributed_dialogue)
        elif "\uff1a" in paragraph or ":" in paragraph:
            character, content = split_dialogue(paragraph)
            if should_treat_as_dialogue(character, known_names):
                beats.append({"type": "dialogue", "character": character, "content": content})
            else:
                beats.append({"type": "action", "content": paragraph})
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


def build_multi_label_beats(paragraph: str, known_names: set[str]) -> list[dict[str, str]]:
    matches = list(LABEL_RE.finditer(paragraph))
    if len(matches) < 2:
        return []

    action_parts = []
    dialogue_beats = []
    for index, match in enumerate(matches):
        name = normalize_label(match.group("name"))
        content_start = match.end()
        content_end = matches[index + 1].start() if index + 1 < len(matches) else len(paragraph)
        content = clean_segment_content(paragraph[content_start:content_end])
        if not content:
            continue
        if should_treat_as_dialogue(name, known_names):
            dialogue_beats.append({"type": "dialogue", "character": name, "content": content})
        elif not is_noise_segment(content):
            action_parts.append(f"{name}\uff1a{content}")

    if not dialogue_beats:
        return []
    if action_parts:
        return [{"type": "action", "content": "\uff1b".join(action_parts)}, *dialogue_beats]
    return dialogue_beats


def parse_attributed_dialogue(paragraph: str, known_names: set[str]) -> dict[str, str] | None:
    match = CHINESE_ATTRIBUTED_DIALOGUE_RE.search(paragraph)
    if match is None:
        return None

    name = normalize_label(match.group("name"))
    if not should_treat_as_dialogue(name, known_names):
        return None

    beat = {
        "type": "dialogue",
        "character": name,
        "content": match.group("content").strip(),
    }
    if parenthetical := match.group("parenthetical"):
        beat["parenthetical"] = parenthetical
    return beat


def should_treat_as_dialogue(name: str, known_names: set[str]) -> bool:
    normalized = normalize_label(name)
    if normalized.lower() in METADATA_LABELS or normalized in METADATA_LABELS:
        return False
    if normalized in GENERIC_NAMES:
        return False
    if known_names:
        return normalized in known_names
    return looks_like_character_name(normalized)


def looks_like_character_name(name: str) -> bool:
    if any(char.isdigit() for char in name):
        return False
    if re.fullmatch(r"[\u4e00-\u9fff]+", name):
        return 1 < len(name) <= 4
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z .'-]{1,31}", name))


def normalize_label(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def clean_segment_content(value: str) -> str:
    return value.strip(" \t\r\n\uff0c,\u3001\uff1b;\u3002")


def is_noise_segment(value: str) -> bool:
    return not value or all(char in "\uff0c,\u3001\uff1b;\u3002" for char in value)


def validate_script(script: ScriptDict) -> None:
    Draft202012Validator(SCRIPT_SCHEMA).validate(script)


def dump_script_yaml(script: ScriptDict) -> str:
    return yaml.safe_dump(script, allow_unicode=True, sort_keys=False)
