from html.parser import HTMLParser
import tempfile
from pathlib import Path

from ebooklib import ITEM_DOCUMENT, epub


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        cleaned = data.strip()
        if cleaned:
            self.parts.append(cleaned)

    def text(self) -> str:
        return "\n".join(self.parts)


def extract_epub_text(data: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as temp_file:
        temp_file.write(data)
        temp_path = Path(temp_file.name)

    try:
        book = epub.read_epub(str(temp_path))
        documents: list[str] = []
        for item in book.get_items_of_type(ITEM_DOCUMENT):
            parser = TextExtractor()
            parser.feed(item.get_content().decode("utf-8", errors="ignore"))
            text = parser.text()
            if text:
                documents.append(text)
        return "\n\n".join(documents).strip()
    finally:
        temp_path.unlink(missing_ok=True)

