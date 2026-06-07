from __future__ import annotations

import json
import re
from typing import Any, Protocol

from anthropic import Anthropic

from converter.prompts import CHAPTER_TO_SCENE_SYSTEM_PROMPT
from converter.services.chapter_splitter import Chapter


VALID_BEAT_TYPES = {"dialogue", "action", "direction"}
FENCED_JSON_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)
MIN_CONTENT_ANCHOR_LENGTH = 3
MAX_CONTENT_ANCHOR_LENGTH = 30


class SceneConversionError(RuntimeError):
    """Raised when an LLM response cannot be turned into a valid scene."""


class SceneConverter(Protocol):
    def convert_chapter(
        self,
        chapter: Chapter,
        characters: list[dict[str, str]],
    ) -> dict[str, object]:
        ...


class ClaudeSceneConverter:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        max_tokens: int,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self.client = client or Anthropic(api_key=api_key)

    def convert_chapter(
        self,
        chapter: Chapter,
        characters: list[dict[str, str]],
    ) -> dict[str, object]:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=0.2,
            system=CHAPTER_TO_SCENE_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": build_chapter_prompt(chapter, characters),
                }
            ],
        )
        response_text = extract_anthropic_response_text(response)
        payload = parse_json_object(response_text)
        return normalize_scene_payload(payload, chapter)


class OpenAICompatibleSceneConverter:
    def __init__(
        self,
        *,
        provider_name: str,
        api_key: str,
        base_url: str,
        model: str,
        max_tokens: int,
        json_mode: bool,
        client: Any | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.model = model
        self.max_tokens = max_tokens
        self.json_mode = json_mode
        if client is not None:
            self.client = client
        else:
            from openai import OpenAI

            self.client = OpenAI(api_key=api_key, base_url=base_url)

    def convert_chapter(
        self,
        chapter: Chapter,
        characters: list[dict[str, str]],
    ) -> dict[str, object]:
        request_body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": CHAPTER_TO_SCENE_SYSTEM_PROMPT},
                {"role": "user", "content": build_chapter_prompt(chapter, characters)},
            ],
            "temperature": 0.2,
            "max_tokens": self.max_tokens,
        }
        if self.json_mode:
            request_body["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**request_body)
        response_text = extract_openai_response_text(response, self.provider_name)
        payload = parse_json_object(response_text)
        return normalize_scene_payload(payload, chapter)


def build_chapter_prompt(chapter: Chapter, characters: list[dict[str, str]]) -> str:
    character_json = json.dumps(characters, ensure_ascii=False, indent=2)
    return (
        "Convert this single novel chapter into one screenplay scene.\n"
        "Do not include the whole script wrapper, act wrapper, markdown, or explanations.\n"
        "Use the source language for title, summary, dialogue, and action beats.\n"
        "Keep the beats concise but specific enough for an author to edit.\n\n"
        "Grounding rules:\n"
        "- Use only the provided chapter text as source material.\n"
        "- Keep beats in the same chronological order as the chapter text; do not move later dialogue before earlier narration.\n"
        "- Treat the character table as source-derived evidence from the full input.\n"
        "- Prefer character names from the table for dialogue beats.\n"
        "- Add a new dialogue character only when that exact name appears in this chapter.\n"
        "- Do not treat object or narration labels as characters, such as 背面写着, 纸条写着, 门禁册显示, or 潮汐表记录.\n"
        "- Do not merge this chapter with other chapters or create act-level structure.\n\n"
        f"Known characters JSON:\n{character_json}\n\n"
        f"Chapter index: {chapter.index}\n"
        f"Chapter title: {chapter.title}\n\n"
        "<chapter_text>\n"
        f"{chapter.text}\n"
        "</chapter_text>"
    )


def extract_anthropic_response_text(response: Any) -> str:
    content = getattr(response, "content", "")
    if isinstance(content, str):
        return content.strip()

    parts: list[str] = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
            continue
        if isinstance(block, dict):
            text = block.get("text", "")
        else:
            text = getattr(block, "text", "")
        if text:
            parts.append(str(text))

    text = "\n".join(parts).strip()
    if not text:
        raise SceneConversionError("anthropic returned an empty response.")
    return text


def extract_openai_response_text(response: Any, provider_name: str) -> str:
    choices = read_attr(response, "choices", [])
    if not choices:
        raise SceneConversionError(f"{provider_name} returned no choices.")

    first_choice = choices[0]
    message = read_attr(first_choice, "message", {})
    content = read_attr(message, "content", "")
    if isinstance(content, list):
        content = "\n".join(read_attr(part, "text", "") for part in content)

    text = str(content).strip()
    if not text:
        raise SceneConversionError(f"{provider_name} returned an empty response.")
    return text


def read_attr(value: Any, key: str, default: Any) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = strip_json_fence(text)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise SceneConversionError("LLM response did not contain a JSON object.") from None
        try:
            payload = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise SceneConversionError("LLM response was not valid JSON.") from exc

    if not isinstance(payload, dict):
        raise SceneConversionError("LLM response JSON must be an object.")
    return payload


def strip_json_fence(text: str) -> str:
    cleaned = text.strip()
    match = FENCED_JSON_RE.match(cleaned)
    if match:
        return match.group(1).strip()
    return cleaned


def normalize_scene_payload(payload: dict[str, Any], chapter: Chapter) -> dict[str, object]:
    beats_payload = payload.get("beats")
    if not isinstance(beats_payload, list) or not beats_payload:
        raise SceneConversionError("LLM scene must include at least one beat.")

    beats = [normalize_beat(beat, index) for index, beat in enumerate(beats_payload, start=1)]
    beats = order_beats_by_source_position(beats, chapter.text)
    summary = clean_text(payload.get("summary")) or first_line(chapter.text)

    return {
        "number": chapter.index,
        "title": clean_text(payload.get("title")) or chapter.title,
        "source_chapter": chapter.index,
        "summary": summary[:240],
        "beats": beats,
    }


def normalize_beat(payload: Any, index: int) -> dict[str, str]:
    if not isinstance(payload, dict):
        raise SceneConversionError(f"Beat {index} must be a JSON object.")

    beat_type = clean_text(payload.get("type"))
    if beat_type not in VALID_BEAT_TYPES:
        raise SceneConversionError(f"Beat {index} has invalid type: {beat_type or '<empty>'}.")

    content = clean_text(payload.get("content"))
    if not content:
        raise SceneConversionError(f"Beat {index} is missing content.")

    beat = {"type": beat_type, "content": content}
    character = clean_text(payload.get("character"))
    parenthetical = clean_text(payload.get("parenthetical"))
    if character:
        beat["character"] = character[:48]
    if parenthetical:
        beat["parenthetical"] = parenthetical[:120]
    return beat


def order_beats_by_source_position(
    beats: list[dict[str, str]],
    chapter_text: str,
) -> list[dict[str, str]]:
    if len(beats) < 2:
        return beats

    normalized_source, source_index_map = normalize_match_text(chapter_text)
    if not normalized_source:
        return beats

    ordered = []
    last_position = -1
    changed = False
    for original_index, beat in enumerate(beats):
        position = find_beat_source_position(beat, normalized_source, source_index_map)
        if position is None:
            position = last_position
        else:
            if position < last_position:
                changed = True
            last_position = position
        ordered.append((position, original_index, beat))

    if not changed:
        return beats

    return [beat for _, _, beat in sorted(ordered, key=lambda item: (item[0], item[1]))]


def find_beat_source_position(
    beat: dict[str, str],
    normalized_source: str,
    source_index_map: list[int],
) -> int | None:
    candidates: list[tuple[int, int]] = []

    content = normalize_match_text(beat.get("content", ""))[0]
    content_match = find_text_anchor_position(content, normalized_source, source_index_map)
    if content_match is not None:
        candidates.append(content_match)

    character = normalize_match_text(beat.get("character", ""))[0]
    if character:
        character_position = unique_source_position(character, normalized_source, source_index_map)
        if character_position is not None:
            candidates.append((len(character) * 2, character_position))

    if not candidates:
        return None

    _, position = max(candidates, key=lambda item: (item[0], -item[1]))
    return position


def find_text_anchor_position(
    text: str,
    normalized_source: str,
    source_index_map: list[int],
) -> tuple[int, int] | None:
    if len(text) < MIN_CONTENT_ANCHOR_LENGTH:
        return None

    exact_index = normalized_source.find(text)
    if exact_index != -1:
        return (len(text) * 3, source_index_map[exact_index])

    max_length = min(MAX_CONTENT_ANCHOR_LENGTH, len(text))
    best: tuple[int, int] | None = None
    seen: set[str] = set()
    for length in range(max_length, MIN_CONTENT_ANCHOR_LENGTH - 1, -1):
        for start in range(0, len(text) - length + 1):
            anchor = text[start : start + length]
            if anchor in seen:
                continue
            seen.add(anchor)
            source_index = normalized_source.find(anchor)
            if source_index == -1:
                continue
            if length == MIN_CONTENT_ANCHOR_LENGTH and normalized_source.count(anchor) > 1:
                continue
            candidate = (length, source_index_map[source_index])
            if best is None or candidate[0] > best[0] or (
                candidate[0] == best[0] and candidate[1] < best[1]
            ):
                best = candidate
        if best is not None:
            return best
    return best


def unique_source_position(
    text: str,
    normalized_source: str,
    source_index_map: list[int],
) -> int | None:
    source_index = normalized_source.find(text)
    if source_index == -1:
        return None
    if normalized_source.find(text, source_index + 1) != -1:
        return None
    return source_index_map[source_index]


def normalize_match_text(text: Any) -> tuple[str, list[int]]:
    normalized_chars: list[str] = []
    source_indices: list[int] = []
    for index, char in enumerate(clean_text(text)):
        if char.isalnum():
            normalized_chars.append(char.lower())
            source_indices.append(index)
    return "".join(normalized_chars), source_indices


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def first_line(text: str) -> str:
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned[:120]
    return "Scene generated from source chapter."
