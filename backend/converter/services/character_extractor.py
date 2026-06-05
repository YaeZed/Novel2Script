from __future__ import annotations

import re
from dataclasses import dataclass, field


SPEAKER_RE = re.compile(
    r"(?m)^\s*(?P<name>[A-Za-z][A-Za-z0-9_ .'-]{0,31}|[\u4e00-\u9fff]{1,8})"
    r"[\uff1a:]\s*(?P<line>\S.+)$"
)
INLINE_SPEAKER_RE = re.compile(
    r"(?m)(?:^|[\s\uff0c,\u3002\uff1b;\u3001])"
    r"(?P<name>[A-Za-z][A-Za-z0-9_ .'-]{0,31}|[\u4e00-\u9fff]{1,8})"
    r"[\uff1a:]\s*(?P<line>[^\uff1a:\n]{1,80})"
)
CHINESE_ATTRIBUTED_DIALOGUE_RE = re.compile(
    r"[\u201c\u300c\u300e][^\u201d\u300d\u300f\n]{1,120}[\u201d\u300d\u300f]"
    r"[\uff0c,]?\s*(?P<name>[\u4e00-\u9fff]{2,4}?)"
    r"(?:\u4f4e\u58f0|\u8f7b\u58f0|\u6c89\u58f0|\u5ffd\u7136)?"
    r"(?:\u8bf4|\u95ee|\u9053|\u558a|\u53eb|\u7b54|\u56de\u7b54|\u7b11\u9053)"
)
CHINESE_PREFACED_DIALOGUE_RE = re.compile(
    r"(?P<name>[\u4e00-\u9fff]{2,4}?)"
    r"(?:\u4f4e\u58f0|\u8f7b\u58f0|\u6c89\u58f0|\u5ffd\u7136)?"
    r"(?:\u8bf4|\u95ee|\u9053|\u558a|\u53eb|\u7b54|\u56de\u7b54|\u7b11\u9053)"
    r"[\uff1a:,\uff0c]\s*[\u201c\u300c\u300e]"
)
CHINESE_ACTION_RE = re.compile(
    r"(?P<name>[\u4e00-\u9fff]{2,4})"
    r"(?:\u62ac\u5934|\u4f4e\u5934|\u56de\u5934|\u8f6c\u8eab|\u6447\u5934|\u70b9\u5934|"
    r"\u76b1\u7709|\u6c89\u9ed8|\u53f9\u6c14|\u7b11\u4e86|\u770b\u89c1|\u770b\u5411|"
    r"\u542c\u89c1|\u63a8\u5f00|\u8d70\u8fdb|\u8d70\u5230|\u7ad9\u5728)"
)
ENGLISH_ATTRIBUTION_RE = re.compile(
    r"(?P<name>[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+"
    r"(?:said|asked|whispered|shouted|replied|muttered)\b"
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
    "\u7b2c\u4e00\u7ae0",
    "\u7b2c\u4e8c\u7ae0",
    "\u7b2c\u4e09\u7ae0",
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
PRONOUNS_AND_GENERIC_NAMES = {
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


@dataclass
class CharacterEvidence:
    name: str
    first_position: int
    speaker_count: int = 0
    attribution_count: int = 0
    action_count: int = 0
    examples: list[str] = field(default_factory=list)

    @property
    def score(self) -> int:
        return self.speaker_count * 4 + self.attribution_count * 3 + self.action_count


def extract_character_table(text: str, limit: int = 12) -> list[dict[str, str]]:
    candidates: dict[str, CharacterEvidence] = {}
    speaker_positions: set[int] = set()

    for match in SPEAKER_RE.finditer(text):
        speaker_positions.add(match.start("name"))
        collect_speaker_match(candidates, match)

    for match in INLINE_SPEAKER_RE.finditer(text):
        if match.start("name") in speaker_positions:
            continue
        collect_speaker_match(candidates, match)

    collect_pattern(candidates, text, CHINESE_ATTRIBUTED_DIALOGUE_RE, "attribution")
    collect_pattern(candidates, text, CHINESE_PREFACED_DIALOGUE_RE, "attribution")
    collect_pattern(candidates, text, ENGLISH_ATTRIBUTION_RE, "attribution")
    collect_pattern(candidates, text, CHINESE_ACTION_RE, "action")

    ranked = sorted(
        candidates.values(),
        key=lambda item: (
            0 if item.speaker_count else 1,
            item.first_position,
            -item.score,
            item.name,
        ),
    )
    return [candidate_to_character(candidate) for candidate in ranked[:limit] if candidate.score > 0]


def collect_speaker_match(
    candidates: dict[str, CharacterEvidence],
    match: re.Match[str],
) -> None:
        name = normalize_name(match.group("name"))
        if not is_character_name(name):
            return
        evidence = get_or_create_candidate(candidates, name, match.start())
        evidence.speaker_count += 1
        add_example(evidence, match.group(0))


def collect_pattern(
    candidates: dict[str, CharacterEvidence],
    text: str,
    pattern: re.Pattern[str],
    evidence_type: str,
) -> None:
    for match in pattern.finditer(text):
        name = normalize_name(match.group("name"))
        if not is_character_name(name):
            continue
        evidence = get_or_create_candidate(candidates, name, match.start())
        if evidence_type == "attribution":
            evidence.attribution_count += 1
        else:
            evidence.action_count += 1
        add_example(evidence, match.group(0))


def get_or_create_candidate(
    candidates: dict[str, CharacterEvidence],
    name: str,
    position: int,
) -> CharacterEvidence:
    existing = candidates.get(name)
    if existing is not None:
        existing.first_position = min(existing.first_position, position)
        return existing

    candidate = CharacterEvidence(name=name, first_position=position)
    candidates[name] = candidate
    return candidate


def add_example(evidence: CharacterEvidence, line: str) -> None:
    cleaned = compact_whitespace(line)
    if cleaned and cleaned not in evidence.examples and len(evidence.examples) < 2:
        evidence.examples.append(cleaned[:80])


def candidate_to_character(evidence: CharacterEvidence) -> dict[str, str]:
    return {
        "name": evidence.name,
        "role": infer_role(evidence),
        "description": build_description(evidence),
    }


def infer_role(evidence: CharacterEvidence) -> str:
    if evidence.speaker_count >= 2 or evidence.score >= 6:
        return "\u4e3b\u8981\u89d2\u8272"
    if evidence.speaker_count:
        return "\u5bf9\u8bdd\u89d2\u8272"
    return "\u53d9\u8ff0\u63d0\u53ca\u89d2\u8272"


def build_description(evidence: CharacterEvidence) -> str:
    parts = []
    if evidence.speaker_count:
        parts.append(f"{evidence.speaker_count} \u5904\u5bf9\u8bdd\u6807\u8bb0")
    if evidence.attribution_count:
        parts.append(f"{evidence.attribution_count} \u5904\u5bf9\u8bdd\u5f52\u56e0")
    if evidence.action_count:
        parts.append(f"{evidence.action_count} \u5904\u53d9\u8ff0\u52a8\u4f5c")

    evidence_text = "\uff1b".join(parts) or "\u539f\u6587\u63d0\u53ca"
    if evidence.examples:
        return f"\u539f\u6587\u8bc1\u636e\uff1a{evidence_text}\u3002\u4f8b\uff1a{evidence.examples[0]}"
    return f"\u539f\u6587\u8bc1\u636e\uff1a{evidence_text}\u3002"


def normalize_name(name: str) -> str:
    return compact_whitespace(name).strip("\u201c\u201d\u300c\u300d\u300e\u300f")


def is_character_name(name: str) -> bool:
    if not name:
        return False
    lowered = name.lower()
    if lowered in METADATA_LABELS or name in PRONOUNS_AND_GENERIC_NAMES:
        return False
    if any(char.isdigit() for char in name):
        return False
    if len(name) > 32:
        return False
    if re.fullmatch(r"[\u4e00-\u9fff]+", name):
        return 1 < len(name) <= 4
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z .'-]{1,31}", name))


def compact_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
