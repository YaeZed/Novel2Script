from __future__ import annotations

from dataclasses import dataclass
from typing import Any


Scene = dict[str, Any]


ACT_TITLES = {
    "single": "\u7b2c\u4e00\u5e55\uff1a\u5168\u7bc7",
    "partial": "\u5df2\u5904\u7406\u90e8\u5206",
    "opening": "\u7b2c\u4e00\u5e55\uff1a\u5f00\u7aef",
    "development": "\u7b2c\u4e8c\u5e55\uff1a\u5c55\u5f00",
    "resolution": "\u7b2c\u4e09\u5e55\uff1a\u6536\u675f",
}


@dataclass(frozen=True)
class ActBoundary:
    number: int
    title: str
    start_scene: int
    end_scene: int
    rationale: str = ""


def assemble_script(
    *,
    title: str,
    characters: list[dict[str, str]],
    scenes: list[Scene],
    act_boundaries: list[ActBoundary] | None = None,
) -> dict[str, Any]:
    normalized_scenes = normalize_scene_sequence(scenes)
    return {
        "title": title,
        "characters": characters,
        "acts": build_acts(normalized_scenes, act_boundaries=act_boundaries),
    }


def assemble_partial_script(
    *,
    title: str,
    characters: list[dict[str, str]],
    scenes: list[Scene],
) -> dict[str, Any]:
    normalized_scenes = normalize_scene_sequence(scenes)
    return {
        "title": title,
        "characters": characters,
        "acts": [
            {
                "number": 1,
                "title": ACT_TITLES["partial"],
                "scenes": normalized_scenes,
            }
        ],
    }


def normalize_scene_sequence(scenes: list[Scene]) -> list[Scene]:
    normalized = []
    for index, scene in enumerate(scenes, start=1):
        normalized_scene = dict(scene)
        normalized_scene["number"] = index
        if "beats" in normalized_scene and isinstance(normalized_scene["beats"], list):
            normalized_scene["beats"] = list(normalized_scene["beats"])
        normalized.append(normalized_scene)
    return normalized


def build_acts(
    scenes: list[Scene],
    *,
    act_boundaries: list[ActBoundary] | None = None,
) -> list[dict[str, Any]]:
    if act_boundaries and validate_act_boundaries(act_boundaries, len(scenes)):
        return build_acts_from_boundaries(scenes, act_boundaries)

    if len(scenes) < 3:
        return [
            {
                "number": 1,
                "title": ACT_TITLES["single"],
                "scenes": scenes,
            }
        ]

    act_slices = split_three_act_slices(len(scenes))
    return [
        {
            "number": 1,
            "title": ACT_TITLES["opening"],
            "scenes": scenes[act_slices[0][0] : act_slices[0][1]],
        },
        {
            "number": 2,
            "title": ACT_TITLES["development"],
            "scenes": scenes[act_slices[1][0] : act_slices[1][1]],
        },
        {
            "number": 3,
            "title": ACT_TITLES["resolution"],
            "scenes": scenes[act_slices[2][0] : act_slices[2][1]],
        },
    ]


def build_acts_from_boundaries(
    scenes: list[Scene],
    boundaries: list[ActBoundary],
) -> list[dict[str, Any]]:
    scene_by_number = {int(scene["number"]): scene for scene in scenes}
    acts = []
    for boundary in boundaries:
        acts.append(
            {
                "number": boundary.number,
                "title": boundary.title,
                "scenes": [
                    scene_by_number[scene_number]
                    for scene_number in range(boundary.start_scene, boundary.end_scene + 1)
                ],
            }
        )
    return acts


def validate_act_boundaries(boundaries: list[ActBoundary], scene_count: int) -> bool:
    if scene_count < 3 or len(boundaries) != 3:
        return False

    expected_start = 1
    for expected_number, boundary in enumerate(boundaries, start=1):
        if boundary.number != expected_number:
            return False
        if boundary.start_scene != expected_start:
            return False
        if boundary.end_scene < boundary.start_scene:
            return False
        if boundary.end_scene > scene_count:
            return False
        expected_start = boundary.end_scene + 1

    return expected_start == scene_count + 1


def split_three_act_slices(scene_count: int) -> list[tuple[int, int]]:
    edge_size = max(1, int(scene_count * 0.25 + 0.5))
    while edge_size * 2 > scene_count - 1:
        edge_size -= 1

    opening_end = edge_size
    resolution_start = scene_count - edge_size
    return [(0, opening_end), (opening_end, resolution_start), (resolution_start, scene_count)]
