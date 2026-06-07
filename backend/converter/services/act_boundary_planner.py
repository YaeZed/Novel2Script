from __future__ import annotations

import json
from typing import Any, Protocol

from anthropic import Anthropic
from django.conf import settings

from converter.prompts import ACT_BOUNDARY_SYSTEM_PROMPT
from converter.services.llm_scene_converter import (
    extract_anthropic_response_text,
    extract_openai_response_text,
    parse_json_object,
)
from converter.services.script_assembler import (
    ACT_TITLES,
    ActBoundary,
    Scene,
    validate_act_boundaries,
)


class ActBoundaryProposalError(RuntimeError):
    """Raised when an LLM response cannot be turned into valid act boundaries."""


class ActBoundaryPlanner(Protocol):
    def propose_boundaries(self, scenes: list[Scene]) -> list[ActBoundary]:
        ...


class ClaudeActBoundaryPlanner:
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

    def propose_boundaries(self, scenes: list[Scene]) -> list[ActBoundary]:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=0.1,
            system=ACT_BOUNDARY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_act_boundary_prompt(scenes)}],
        )
        response_text = extract_anthropic_response_text(response)
        return normalize_act_boundary_payload(parse_json_object(response_text), len(scenes))


class OpenAICompatibleActBoundaryPlanner:
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

    def propose_boundaries(self, scenes: list[Scene]) -> list[ActBoundary]:
        request_body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": ACT_BOUNDARY_SYSTEM_PROMPT},
                {"role": "user", "content": build_act_boundary_prompt(scenes)},
            ],
            "temperature": 0.1,
            "max_tokens": self.max_tokens,
        }
        if self.json_mode:
            request_body["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**request_body)
        response_text = extract_openai_response_text(response, self.provider_name)
        return normalize_act_boundary_payload(parse_json_object(response_text), len(scenes))


def build_act_boundary_planner(provider: str) -> ActBoundaryPlanner | None:
    if provider == "placeholder":
        return None

    if provider == "anthropic":
        return ClaudeActBoundaryPlanner(
            api_key=settings.ANTHROPIC_API_KEY.strip(),
            model=settings.ANTHROPIC_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
        )

    if provider == "openai":
        return OpenAICompatibleActBoundaryPlanner(
            provider_name="openai",
            api_key=settings.OPENAI_API_KEY.strip(),
            base_url=settings.OPENAI_BASE_URL,
            model=settings.OPENAI_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            json_mode=settings.OPENAI_JSON_MODE,
        )

    if provider == "qwen":
        return OpenAICompatibleActBoundaryPlanner(
            provider_name="qwen",
            api_key=settings.QWEN_API_KEY.strip(),
            base_url=settings.QWEN_BASE_URL,
            model=settings.QWEN_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            json_mode=settings.QWEN_JSON_MODE,
        )

    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


def propose_act_boundaries_safely(
    planner: ActBoundaryPlanner | None,
    scenes: list[Scene],
) -> list[ActBoundary] | None:
    if planner is None or len(scenes) < 3:
        return None

    try:
        boundaries = planner.propose_boundaries(scenes)
    except Exception:
        return None

    if not validate_act_boundaries(boundaries, len(scenes)):
        return None
    return boundaries


def build_act_boundary_prompt(scenes: list[Scene]) -> str:
    outline = [scene_to_outline(scene) for scene in scenes]
    return (
        "Choose three-act boundaries for this already generated script.\n"
        "Use story events, escalation, reversals, and resolution cues rather than equal scene counts.\n"
        "Return only JSON that matches the required schema.\n\n"
        f"Scene count: {len(scenes)}\n"
        f"Scene outline JSON:\n{json.dumps(outline, ensure_ascii=False, indent=2)}"
    )


def scene_to_outline(scene: Scene) -> dict[str, object]:
    beats = scene.get("beats")
    return {
        "number": scene.get("number"),
        "source_chapter": scene.get("source_chapter"),
        "title": truncate_text(scene.get("title"), 80),
        "summary": truncate_text(scene.get("summary"), 180),
        "beats": [beat_to_outline(beat) for beat in beats[:8]] if isinstance(beats, list) else [],
    }


def beat_to_outline(beat: Any) -> dict[str, str]:
    if not isinstance(beat, dict):
        return {"type": "action", "content": truncate_text(beat, 120)}
    outline = {
        "type": truncate_text(beat.get("type"), 24),
        "content": truncate_text(beat.get("content"), 120),
    }
    if character := truncate_text(beat.get("character"), 48):
        outline["character"] = character
    return outline


def normalize_act_boundary_payload(payload: dict[str, Any], scene_count: int) -> list[ActBoundary]:
    acts = payload.get("acts")
    if not isinstance(acts, list):
        raise ActBoundaryProposalError("Act boundary response must include an acts array.")

    default_titles = [ACT_TITLES["opening"], ACT_TITLES["development"], ACT_TITLES["resolution"]]
    boundaries = []
    for index, act in enumerate(acts, start=1):
        if not isinstance(act, dict):
            raise ActBoundaryProposalError(f"Act {index} must be a JSON object.")
        boundaries.append(
            ActBoundary(
                number=parse_int(act.get("number"), f"Act {index} number"),
                title=default_titles[index - 1] if index <= len(default_titles) else f"Act {index}",
                start_scene=parse_int(act.get("start_scene"), f"Act {index} start_scene"),
                end_scene=parse_int(act.get("end_scene"), f"Act {index} end_scene"),
                rationale=truncate_text(act.get("rationale"), 240),
            )
        )

    if not validate_act_boundaries(boundaries, scene_count):
        raise ActBoundaryProposalError("Act boundaries must cover every scene exactly once.")
    return boundaries


def parse_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or value is None:
        raise ActBoundaryProposalError(f"{field_name} must be an integer.")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ActBoundaryProposalError(f"{field_name} must be an integer.") from exc


def truncate_text(value: Any, max_length: int) -> str:
    if value is None:
        return ""
    return str(value).strip()[:max_length]
