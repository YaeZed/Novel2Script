from dataclasses import dataclass
from html.parser import HTMLParser
import tempfile
from pathlib import Path
import re

from ebooklib import ITEM_DOCUMENT, epub

from converter.services.chapter_splitter import looks_like_chapter_heading


BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "chapter",
    "dd",
    "div",
    "dt",
    "figcaption",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "p",
    "pre",
    "section",
    "table",
    "td",
    "th",
    "title",
    "tr",
}
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "title"}
SKIP_TAGS = {"script", "style"}
AUXILIARY_NAME_PARTS = ("cover", "copyright", "nav", "toc")
AUXILIARY_TITLES = {"目录", "目錄", "table of contents", "contents", "copyright"}
NON_STORY_TITLE_PARTS = (
    "版权信息",
    "版权申明",
    "版权声明",
    "出版说明",
    "译序",
    "代跋",
    "年谱",
    "音乐列表",
)


@dataclass(frozen=True)
class EpubDocumentText:
    title: str
    text: str


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []
        self.current_parts: list[str] = []
        self.heading_parts: list[str] = []
        self.title = ""
        self.current_tag = ""
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001, ARG002
        normalized_tag = tag.lower()
        if normalized_tag in SKIP_TAGS:
            self.skip_depth += 1
            return
        if normalized_tag in BLOCK_TAGS:
            self.flush_current()
        self.current_tag = normalized_tag
        if normalized_tag in HEADING_TAGS:
            self.heading_parts = []

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        if normalized_tag in SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if normalized_tag in HEADING_TAGS and self.heading_parts and not self.title:
            self.title = clean_inline_text(" ".join(self.heading_parts))
        if normalized_tag in BLOCK_TAGS:
            self.flush_current()
        self.current_tag = ""

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        cleaned = clean_inline_text(data)
        if not cleaned:
            return
        if self.current_tag in HEADING_TAGS:
            self.heading_parts.append(cleaned)
        if self.current_tag == "title":
            return
        self.current_parts.append(cleaned)

    def text(self) -> str:
        self.flush_current()
        return "\n".join(self.lines)

    def flush_current(self) -> None:
        line = clean_inline_text(" ".join(self.current_parts))
        if line:
            self.lines.append(line)
        self.current_parts = []


def extract_epub_text(data: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as temp_file:
        temp_file.write(data)
        temp_path = Path(temp_file.name)

    try:
        book = epub.read_epub(str(temp_path))
        documents = extract_ordered_documents(book)
        return render_documents_as_chapter_text(documents)
    finally:
        temp_path.unlink(missing_ok=True)


def extract_ordered_documents(book) -> list[EpubDocumentText]:  # noqa: ANN001
    documents: list[EpubDocumentText] = []
    seen: set[str] = set()

    for item in iter_spine_document_items(book):
        identity = item_identity(item)
        if identity in seen:
            continue
        seen.add(identity)
        document = extract_document_text(item)
        if document and not is_auxiliary_document(item, document):
            documents.append(document)

    for item in book.get_items_of_type(ITEM_DOCUMENT):
        identity = item_identity(item)
        if identity in seen:
            continue
        seen.add(identity)
        document = extract_document_text(item)
        if document and not is_auxiliary_document(item, document):
            documents.append(document)

    return documents


def iter_spine_document_items(book):  # noqa: ANN001
    for spine_entry in getattr(book, "spine", []):
        item_id = spine_entry[0] if isinstance(spine_entry, tuple) else spine_entry
        item = book.get_item_with_id(item_id)
        if item is not None and item.get_type() == ITEM_DOCUMENT:
            yield item


def extract_document_text(item) -> EpubDocumentText | None:  # noqa: ANN001
    parser = TextExtractor()
    parser.feed(item.get_content().decode("utf-8", errors="ignore"))
    text = parser.text().strip()
    if not text:
        return None
    return EpubDocumentText(title=parser.title.strip(), text=text)


def render_documents_as_chapter_text(documents: list[EpubDocumentText]) -> str:
    if not documents:
        return ""
    if len(documents) == 1:
        return documents[0].text

    rendered_sections: list[str] = []
    for index, document in enumerate(documents, start=1):
        heading = document.title if document.title else f"EPUB 章节 {index}"
        if not looks_like_chapter_heading(heading):
            heading = f"第{index}章 {heading}"

        text = document.text
        first_line = text.splitlines()[0].strip() if text.splitlines() else ""
        if looks_like_chapter_heading(first_line):
            rendered_sections.append(text)
        else:
            rendered_sections.append(f"{heading}\n{text}")

    return "\n\n".join(rendered_sections).strip()


def item_identity(item) -> str:  # noqa: ANN001
    if hasattr(item, "get_id"):
        item_id = item.get_id()
        if item_id:
            return str(item_id)
    if hasattr(item, "get_name"):
        name = item.get_name()
        if name:
            return str(name)
    return str(id(item))


def is_auxiliary_document(item, document: EpubDocumentText) -> bool:  # noqa: ANN001
    name = item.get_name().lower() if hasattr(item, "get_name") else ""
    title = document.title.strip().lower()
    if any(part in name for part in AUXILIARY_NAME_PARTS) and len(document.text) < 2000:
        return True
    if title in AUXILIARY_TITLES and len(document.text) < 2000:
        return True
    return is_non_story_document(document)


def is_non_story_document(document: EpubDocumentText) -> bool:
    text = document.text.strip()
    first_line = first_meaningful_line(text)
    label_source = f"{document.title}\n{first_line}"
    if any(part in label_source for part in NON_STORY_TITLE_PARTS):
        return True
    if len(text) < 2500 and "书名：" in text and "作者：" in text:
        return True
    if len(text) < 2000 and "出版社" in text and ("digital lab" in text.lower() or "版权" in text):
        return True
    return is_chronology_document(first_line, text)


def first_meaningful_line(text: str) -> str:
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned
    return ""


def is_chronology_document(first_line: str, text: str) -> bool:
    if not first_line:
        return False
    if "年谱" in first_line:
        return True
    if re.match(r"^\d{4}年\s+\d+岁$", first_line):
        return any(keyword in text for keyword in ("出版", "获", "入", "移居", "旅行", "大学"))
    return False


def clean_inline_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

