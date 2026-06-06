from __future__ import annotations

from typing import Any


Scene = dict[str, Any]


ACT_TITLES = {
    "single": "\u7b2c\u4e00\u5e55\uff1a\u5168\u7bc7",
    "opening": "\u7b2c\u4e00\u5e55\uff1a\u5f00\u7aef",
    "development": "\u7b2c\u4e8c\u5e55\uff1a\u5c55\u5f00",
    "resolution": "\u7b2c\u4e09\u5e55\uff1a\u6536\u675f",
}


def assemble_script(
    *,
    title: str,
    characters: list[dict[str, str]],
    scenes: list[Scene],
) -> dict[str, Any]:
    normalized_scenes = normalize_scene_sequence(scenes)
    return {
        "title": title,
        "characters": characters,
        "acts": build_acts(normalized_scenes),
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


def build_acts(scenes: list[Scene]) -> list[dict[str, Any]]:
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


def split_three_act_slices(scene_count: int) -> list[tuple[int, int]]:
    edge_size = max(1, int(scene_count * 0.25 + 0.5))
    while edge_size * 2 > scene_count - 1:
        edge_size -= 1

    opening_end = edge_size
    resolution_start = scene_count - edge_size
    return [(0, opening_end), (opening_end, resolution_start), (resolution_start, scene_count)]
