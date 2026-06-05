from dataclasses import dataclass
import re


CHAPTER_HEADING_RE = re.compile(
    r"(?m)^(第[一二三四五六七八九十百千万0-9０-９]+[章节回卷部].*)$"
)


@dataclass(frozen=True)
class Chapter:
    index: int
    title: str
    text: str


def split_chapters(text: str) -> list[Chapter]:
    normalized = normalize_text(text)
    matches = list(CHAPTER_HEADING_RE.finditer(normalized))

    if not matches:
        return [Chapter(index=1, title="全文", text=normalized)]

    chapters: list[Chapter] = []
    preface = normalized[: matches[0].start()].strip()
    if preface:
        chapters.append(Chapter(index=1, title="序章", text=preface))

    for match_index, match in enumerate(matches):
        start = match.end()
        end = matches[match_index + 1].start() if match_index + 1 < len(matches) else len(normalized)
        content = normalized[start:end].strip()
        if content:
            chapters.append(
                Chapter(
                    index=len(chapters) + 1,
                    title=match.group(1).strip(),
                    text=content,
                )
            )

    return chapters or [Chapter(index=1, title="全文", text=normalized)]


def normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    compact_lines: list[str] = []

    for line in lines:
        if line or (compact_lines and compact_lines[-1]):
            compact_lines.append(line)

    return "\n".join(compact_lines).strip()

