from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase, override_settings
from ebooklib import ITEM_DOCUMENT

from converter.models import ConversionTask
from converter.services.chapter_splitter import Chapter, split_chapters
from converter.services.epub_parser import extract_epub_text
from converter.services.llm_scene_converter import (
    ClaudeSceneConverter,
    OpenAICompatibleSceneConverter,
    SceneConversionError,
)
from converter.services.pipeline import build_scene_converter, run_conversion_task


SAMPLE_TEXT = (
    "\u7b2c\u4e00\u7ae0 \u96e8\u591c\n"
    "\u96e8\u58f0\u843d\u5728\u65e7\u620f\u9662\u7684\u73bb\u7483\u68da\u9876\u4e0a\u3002\n"
    "\u6797\u7167\uff1a\u4eca\u665a\u4e0d\u80fd\u518d\u7b49\u4e86\u3002\n"
    "\u6c88\u5c9a\u62ac\u5934\uff0c\u770b\u89c1\u540e\u53f0\u95e8\u7f1d\u91cc\u6f0f\u51fa\u4e00\u7ebf\u51b7\u5149\u3002\n\n"
    "\u7b2c\u4e8c\u7ae0 \u540e\u53f0\n"
    "\u6c88\u5c9a\uff1a\u4f60\u542c\u89c1\u4e86\u5417\uff1f"
)


class ChapterSplitterTests(TestCase):
    def test_splits_chinese_chapter_headings(self) -> None:
        chapters = split_chapters(SAMPLE_TEXT)

        self.assertEqual(len(chapters), 2)
        self.assertEqual(chapters[0].index, 1)
        self.assertIn("\u96e8\u591c", chapters[0].title)

    def test_splits_common_preface_and_english_headings(self) -> None:
        text = (
            "楔子\n"
            "旧戏院还没有开灯。\n\n"
            "CHAPTER 2: Backstage\n"
            "Shen Lan heard a sound behind the curtain.\n"
        )

        chapters = split_chapters(text)

        self.assertEqual(len(chapters), 2)
        self.assertEqual(chapters[0].title, "楔子")
        self.assertEqual(chapters[1].title, "CHAPTER 2: Backstage")

    def test_chunks_long_text_without_headings(self) -> None:
        paragraphs = [f"段落{i} " + ("雨" * 90) for i in range(20)]

        chapters = split_chapters("\n".join(paragraphs), chunk_char_limit=1000)

        self.assertGreater(len(chapters), 1)
        self.assertTrue(chapters[0].title.startswith("全文（分块 1/"))
        self.assertLessEqual(len(chapters[0].text), 1000)


class FakeEpubItem:
    def __init__(self, item_id: str, name: str, html: str) -> None:
        self.item_id = item_id
        self.name = name
        self.html = html

    def get_id(self) -> str:
        return self.item_id

    def get_name(self) -> str:
        return self.name

    def get_type(self) -> int:
        return ITEM_DOCUMENT

    def get_content(self) -> bytes:
        return self.html.encode("utf-8")


class FakeEpubBook:
    def __init__(self, items: list[FakeEpubItem], spine: list[tuple[str, str]]) -> None:
        self.items = {item.get_id(): item for item in items}
        self.spine = spine

    def get_item_with_id(self, item_id: str) -> FakeEpubItem | None:
        return self.items.get(item_id)

    def get_items_of_type(self, item_type: int) -> list[FakeEpubItem]:
        return [item for item in self.items.values() if item.get_type() == item_type]


class EpubParserTests(TestCase):
    def test_extracts_epub_documents_in_spine_order(self) -> None:
        nav = FakeEpubItem(
            "nav",
            "nav.xhtml",
            "<html><body><h1>目录</h1><p>第一章</p><p>第二章</p></body></html>",
        )
        first = FakeEpubItem(
            "chapter-1",
            "chapter1.xhtml",
            "<html><head><title>Rain Night</title></head><body><p>雨落在旧戏院。</p></body></html>",
        )
        second = FakeEpubItem(
            "chapter-2",
            "chapter2.xhtml",
            "<html><head><title>Backstage</title></head><body><p>后台门缝透出冷光。</p></body></html>",
        )
        book = FakeEpubBook(
            items=[second, nav, first],
            spine=[("chapter-1", "yes"), ("chapter-2", "yes"), ("nav", "yes")],
        )

        with patch("converter.services.epub_parser.epub.read_epub", return_value=book):
            text = extract_epub_text(b"fake epub bytes")

        self.assertIn("第1章 Rain Night", text)
        self.assertIn("第2章 Backstage", text)
        self.assertLess(text.index("第1章 Rain Night"), text.index("第2章 Backstage"))
        self.assertNotIn("目录", text)

        chapters = split_chapters(text)
        self.assertEqual([chapter.title for chapter in chapters], ["第1章 Rain Night", "第2章 Backstage"])


class FakeClaudeMessages:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(content=[SimpleNamespace(text=self.response_text)])


class FakeClaudeClient:
    def __init__(self, response_text: str) -> None:
        self.messages = FakeClaudeMessages(response_text)


class FakeOpenAICompletions:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self.response_text),
                )
            ]
        )


class FakeOpenAIClient:
    def __init__(self, response_text: str) -> None:
        self.chat = SimpleNamespace(completions=FakeOpenAICompletions(response_text))


class ClaudeSceneConverterTests(TestCase):
    def test_converts_claude_json_response_to_scene(self) -> None:
        client = FakeClaudeClient(
            """
            {
              "title": "\u96e8\u591c\u5bf9\u5cd9",
              "summary": "\u6797\u7167\u5728\u65e7\u620f\u9662\u903c\u8fd1\u771f\u76f8\u3002",
              "beats": [
                {"type": "action", "content": "\u96e8\u58f0\u538b\u8fc7\u65e7\u620f\u9662\u7684\u7a7a\u54cd\u3002"},
                {"type": "dialogue", "character": "\u6797\u7167", "content": "\u4eca\u665a\u4e0d\u80fd\u518d\u7b49\u4e86\u3002"}
              ]
            }
            """
        )
        converter = ClaudeSceneConverter(
            api_key="test-key",
            model="claude-test",
            max_tokens=1000,
            client=client,
        )
        chapter = Chapter(index=1, title="\u7b2c\u4e00\u7ae0 \u96e8\u591c", text=SAMPLE_TEXT)

        scene = converter.convert_chapter(chapter, [{"name": "\u6797\u7167", "role": "\u5f85\u5b9a"}])

        self.assertEqual(scene["number"], 1)
        self.assertEqual(scene["source_chapter"], 1)
        self.assertEqual(scene["title"], "\u96e8\u591c\u5bf9\u5cd9")
        self.assertEqual(scene["beats"][1]["character"], "\u6797\u7167")
        call = client.messages.calls[0]
        self.assertEqual(call["model"], "claude-test")
        self.assertIn("\u7b2c\u4e00\u7ae0 \u96e8\u591c", call["messages"][0]["content"])

    def test_invalid_claude_response_raises_clear_error(self) -> None:
        converter = ClaudeSceneConverter(
            api_key="test-key",
            model="claude-test",
            max_tokens=1000,
            client=FakeClaudeClient("not json"),
        )
        chapter = Chapter(index=1, title="\u5168\u6587", text="text")

        with self.assertRaises(SceneConversionError):
            converter.convert_chapter(chapter, [])


class OpenAICompatibleSceneConverterTests(TestCase):
    def test_converts_openai_compatible_response_to_scene(self) -> None:
        client = FakeOpenAIClient(
            """
            {
              "title": "\u540e\u53f0\u95e8\u7f1d",
              "summary": "\u6c88\u5c9a\u5728\u540e\u53f0\u542c\u89c1\u5f02\u54cd\u3002",
              "beats": [
                {"type": "action", "content": "\u95e8\u7f1d\u91cc\u6f0f\u51fa\u51b7\u5149\u3002"},
                {"type": "dialogue", "character": "\u6c88\u5c9a", "content": "\u4f60\u542c\u89c1\u4e86\u5417\uff1f"}
              ]
            }
            """
        )
        converter = OpenAICompatibleSceneConverter(
            provider_name="qwen",
            api_key="test-key",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-plus",
            max_tokens=1000,
            json_mode=True,
            client=client,
        )
        chapter = Chapter(index=2, title="\u7b2c\u4e8c\u7ae0 \u540e\u53f0", text=SAMPLE_TEXT)

        scene = converter.convert_chapter(chapter, [{"name": "\u6c88\u5c9a", "role": "\u5f85\u5b9a"}])

        self.assertEqual(scene["number"], 2)
        self.assertEqual(scene["title"], "\u540e\u53f0\u95e8\u7f1d")
        self.assertEqual(scene["beats"][1]["character"], "\u6c88\u5c9a")
        call = client.chat.completions.calls[0]
        self.assertEqual(call["model"], "qwen-plus")
        self.assertEqual(call["response_format"], {"type": "json_object"})

    def test_can_skip_json_mode_for_providers_with_partial_compatibility(self) -> None:
        client = FakeOpenAIClient(
            '{"title":"\u540e\u53f0","summary":"\u5f02\u54cd\u51fa\u73b0","beats":[{"type":"action","content":"\u95e8\u7f1d\u53d1\u5149\u3002"}]}'
        )
        converter = OpenAICompatibleSceneConverter(
            provider_name="qwen",
            api_key="test-key",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-plus",
            max_tokens=1000,
            json_mode=False,
            client=client,
        )

        converter.convert_chapter(Chapter(index=1, title="\u5168\u6587", text="text"), [])

        call = client.chat.completions.calls[0]
        self.assertNotIn("response_format", call)


class ConversionApiTests(TestCase):
    @override_settings(
        LLM_PROVIDER="auto",
        ANTHROPIC_API_KEY="",
        OPENAI_API_KEY="",
        QWEN_API_KEY="",
    )
    def test_convert_text_uses_placeholder_generator_without_api_key(self) -> None:
        created = self.client.post("/api/convert", {"text": SAMPLE_TEXT})

        self.assertEqual(created.status_code, 201)
        task_id = created.json()["task_id"]
        status_response = self.client.get(f"/api/status/{task_id}")
        result_response = self.client.get(f"/api/result/{task_id}")

        self.assertEqual(status_response.json()["status"], "completed")
        self.assertEqual(status_response.json()["llm_provider"], "placeholder")
        result = result_response.json()
        self.assertEqual(result["status"], "completed")
        self.assertIn("script_yaml", result)
        self.assertEqual(result["characters"][0]["name"], "\u6797\u7167")

    def test_convert_failure_sanitizes_provider_auth_error(self) -> None:
        raw_error = (
            "Error code: 401 - {'error': {'message': 'Incorrect API key provided: "
            "sk_a79fb********************************52c8. You can find your API key at "
            "https://platform.openai.com/account/api-keys.', 'code': 'invalid_api_key'}}"
        )

        with patch("converter.views.run_conversion_task", side_effect=Exception(raw_error)):
            created = self.client.post("/api/convert", {"text": SAMPLE_TEXT})

        task_id = created.json()["task_id"]
        status_response = self.client.get(f"/api/status/{task_id}")
        error_message = status_response.json()["error_message"]

        self.assertEqual(status_response.json()["status"], "failed")
        self.assertIn("OpenAI API key 无效", error_message)
        self.assertIn("LLM_PROVIDER=placeholder", error_message)
        self.assertNotIn("sk_a79fb", error_message)
        self.assertNotIn("platform.openai.com", error_message)
        self.assertNotIn("invalid_api_key", error_message)

    @override_settings(
        LLM_PROVIDER="qwen",
        ANTHROPIC_API_KEY="",
        OPENAI_API_KEY="",
        QWEN_API_KEY="",
    )
    def test_status_reports_misconfigured_provider_without_crashing(self) -> None:
        task = ConversionTask.objects.create(
            input_name="sample.txt",
            source_text=SAMPLE_TEXT,
            status=ConversionTask.Status.FAILED,
            error_message="config failed",
            progress=100,
        )

        status_response = self.client.get(f"/api/status/{task.id}")

        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()["llm_provider"], "misconfigured")


class ConversionPipelineTests(TestCase):
    @override_settings(
        LLM_PROVIDER="placeholder",
        ANTHROPIC_API_KEY="real-looking-key",
        OPENAI_API_KEY="real-looking-key",
        QWEN_API_KEY="real-looking-key",
    )
    def test_placeholder_provider_never_uses_external_keys(self) -> None:
        converter = build_scene_converter()

        self.assertEqual(converter.__class__.__name__, "PlaceholderSceneConverter")

    @override_settings(
        LLM_PROVIDER="qwen",
        ANTHROPIC_API_KEY="",
        OPENAI_API_KEY="",
        QWEN_API_KEY="",
    )
    def test_explicit_provider_requires_matching_key(self) -> None:
        with self.assertRaisesMessage(ValueError, "LLM_PROVIDER=qwen requires its API key"):
            build_scene_converter()

    @override_settings(
        ANTHROPIC_API_KEY="test-key",
        OPENAI_API_KEY="",
        QWEN_API_KEY="",
        LLM_PROVIDER="anthropic",
        ANTHROPIC_MODEL="claude-test",
        LLM_MAX_TOKENS=1000,
    )
    def test_pipeline_uses_claude_converter_when_api_key_exists(self) -> None:
        task = ConversionTask.objects.create(
            input_name="sample.txt",
            source_text=SAMPLE_TEXT,
        )

        with patch("converter.services.pipeline.ClaudeSceneConverter") as converter_class:
            converter = converter_class.return_value
            converter.convert_chapter.side_effect = [
                {
                    "number": 1,
                    "title": "\u96e8\u591c\u5bf9\u5cd9",
                    "source_chapter": 1,
                    "summary": "\u6797\u7167\u5f00\u573a\u3002",
                    "beats": [{"type": "action", "content": "\u96e8\u58f0\u538b\u4e0b\u6765\u3002"}],
                },
                {
                    "number": 2,
                    "title": "\u540e\u53f0\u56de\u58f0",
                    "source_chapter": 2,
                    "summary": "\u6c88\u5c9a\u542c\u89c1\u5f02\u54cd\u3002",
                    "beats": [{"type": "dialogue", "character": "\u6c88\u5c9a", "content": "\u4f60\u542c\u89c1\u4e86\u5417\uff1f"}],
                },
            ]

            run_conversion_task(task)

        task.refresh_from_db()
        converter_class.assert_called_once_with(
            api_key="test-key",
            model="claude-test",
            max_tokens=1000,
        )
        self.assertEqual(converter.convert_chapter.call_count, 2)
        self.assertEqual(task.status, "completed")
        self.assertEqual(task.chapters_done, 2)
        self.assertIn("\u96e8\u591c\u5bf9\u5cd9", task.script_yaml)

    @override_settings(
        LLM_PROVIDER="qwen",
        ANTHROPIC_API_KEY="",
        OPENAI_API_KEY="",
        QWEN_API_KEY="dashscope-key",
        QWEN_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1",
        QWEN_MODEL="qwen-plus",
        LLM_MAX_TOKENS=1000,
        QWEN_JSON_MODE=False,
    )
    def test_scene_converter_uses_qwen_config(self) -> None:
        with patch("converter.services.pipeline.OpenAICompatibleSceneConverter") as converter_class:
            converter = build_scene_converter()

        self.assertEqual(converter, converter_class.return_value)
        converter_class.assert_called_once_with(
            provider_name="qwen",
            api_key="dashscope-key",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-plus",
            max_tokens=1000,
            json_mode=False,
        )

    @override_settings(
        LLM_PROVIDER="openai",
        ANTHROPIC_API_KEY="",
        OPENAI_API_KEY="openai-key",
        OPENAI_BASE_URL="https://api.openai.com/v1",
        OPENAI_MODEL="gpt-4.1-mini",
        OPENAI_JSON_MODE=True,
        QWEN_API_KEY="",
        LLM_MAX_TOKENS=1000,
    )
    def test_scene_converter_uses_openai_config(self) -> None:
        with patch("converter.services.pipeline.OpenAICompatibleSceneConverter") as converter_class:
            converter = build_scene_converter()

        self.assertEqual(converter, converter_class.return_value)
        converter_class.assert_called_once_with(
            provider_name="openai",
            api_key="openai-key",
            base_url="https://api.openai.com/v1",
            model="gpt-4.1-mini",
            max_tokens=1000,
            json_mode=True,
        )
