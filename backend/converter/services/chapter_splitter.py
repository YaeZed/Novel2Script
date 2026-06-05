from dataclasses import dataclass
import re


DEFAULT_CHUNK_CHAR_LIMIT = 4500

CHAPTER_HEADING_RE = re.compile(
    r"(?im)^[^\S\n]*("
    r"第[^\S\n]*[一二三四五六七八九十百千万零〇两0-9０-９]+[^\S\n]*[章节回卷部集][^\S\n]*[^\n]{0,80}"
    r"|(?:序章|楔子|引子|尾声|后记|番外)(?:[^\S\n]+[^\n]{1,80})?"
    r"|chapter[^\S\n]+[0-9ivxlcdm]+(?:[^\S\n]*[:：.\-][^\S\n]*[^\n]{0,80})?"
    r"|[0-9０-９]{1,4}[^\S\n]*[.、][^\S\n]*[^\n]{1,80}"
    r")[^\S\n]*$"
)


@dataclass(frozen=True)
class Chapter:
    index: int
    title: str
    text: str


def split_chapters(text: str, chunk_char_limit: int = DEFAULT_CHUNK_CHAR_LIMIT) -> list[Chapter]:
    normalized = normalize_text(text)
    matches = list(CHAPTER_HEADING_RE.finditer(normalized))

    if not normalized:
        return [Chapter(index=1, title="全文", text="")]

    if not matches:
        return build_chunked_chapters("全文", normalized, chunk_char_limit)

    chapters: list[Chapter] = []
    preface = normalized[: matches[0].start()].strip()
    if preface:
        append_chunked_chapter(chapters, "序章", preface, chunk_char_limit)

    for match_index, match in enumerate(matches):
        start = match.end()
        end = matches[match_index + 1].start() if match_index + 1 < len(matches) else len(normalized)
        content = normalized[start:end].strip()
        if content:
            append_chunked_chapter(chapters, match.group(1).strip(), content, chunk_char_limit)

    return chapters or build_chunked_chapters("全文", normalized, chunk_char_limit)


def looks_like_chapter_heading(line: str) -> bool:
    return bool(CHAPTER_HEADING_RE.match(line.strip()))


def normalize_text(text: str) -> str:
    cleaned_text = text.replace("\ufeff", "").replace("\u3000", " ")
    lines = [
        re.sub(r"[ \t]+", " ", line).strip()
        for line in cleaned_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    ]
    compact_lines: list[str] = []

    for line in lines:
        if line or (compact_lines and compact_lines[-1]):
            compact_lines.append(line)

    return "\n".join(compact_lines).strip()


def append_chunked_chapter(
    chapters: list[Chapter],
    title: str,
    text: str,
    chunk_char_limit: int,
) -> None:
    for chunk_title, chunk_text in build_chunked_chapter_parts(title, text, chunk_char_limit):
        chapters.append(Chapter(index=len(chapters) + 1, title=chunk_title, text=chunk_text))


def build_chunked_chapters(title: str, text: str, chunk_char_limit: int) -> list[Chapter]:
    return [
        Chapter(index=index + 1, title=chunk_title, text=chunk_text)
        for index, (chunk_title, chunk_text) in enumerate(
            build_chunked_chapter_parts(title, text, chunk_char_limit)
        )
    ]


def build_chunked_chapter_parts(
    title: str,
    text: str,
    chunk_char_limit: int,
) -> list[tuple[str, str]]:
    chunks = chunk_text(text, chunk_char_limit)
    if len(chunks) == 1:
        return [(title, chunks[0])]
    return [(f"{title}（分块 {index + 1}/{len(chunks)}）", chunk) for index, chunk in enumerate(chunks)]


def chunk_text(text: str, chunk_char_limit: int) -> list[str]:
    limit = max(1000, chunk_char_limit)
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n+", text) if paragraph.strip()]
    if not paragraphs:
        return [text.strip()]

    chunks: list[str] = []
    current: list[str] = []
    current_length = 0

    for paragraph in paragraphs:
        if len(paragraph) > limit:
            if current:
                chunks.append("\n".join(current))
                current = []
                current_length = 0
            chunks.extend(slice_long_paragraph(paragraph, limit))
            continue

        next_length = current_length + len(paragraph) + (1 if current else 0)
        if current and next_length > limit:
            chunks.append("\n".join(current))
            current = [paragraph]
            current_length = len(paragraph)
        else:
            current.append(paragraph)
            current_length = next_length

    if current:
        chunks.append("\n".join(current))

    return chunks or [text.strip()]


def slice_long_paragraph(paragraph: str, limit: int) -> list[str]:
    return [paragraph[start : start + limit].strip() for start in range(0, len(paragraph), limit)]

