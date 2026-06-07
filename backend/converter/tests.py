from types import SimpleNamespace
from unittest.mock import patch

import yaml
from django.test import TestCase, override_settings
from ebooklib import ITEM_DOCUMENT

from converter.models import ConversionTask
from converter.services.act_boundary_planner import (
    build_act_boundary_planner,
    build_act_boundary_prompt,
    normalize_act_boundary_payload,
)
from converter.services.character_extractor import extract_character_table
from converter.services.chapter_splitter import Chapter, split_chapters
from converter.services.epub_parser import extract_epub_text
from converter.services.llm_scene_converter import (
    ClaudeSceneConverter,
    OpenAICompatibleSceneConverter,
    SceneConversionError,
    build_chapter_prompt,
)
from converter.services.pipeline import PlaceholderSceneConverter, build_scene_converter, run_conversion_task
from converter.services.script_assembler import ActBoundary, assemble_partial_script, assemble_script


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


class CharacterExtractorTests(TestCase):
    def test_extracts_dialogue_and_narration_evidence(self) -> None:
        text = (
            "\u7b2c\u4e00\u7ae0 \u96e8\u591c\n"
            "\u6807\u9898\uff1a\u4e0d\u5e94\u8be5\u662f\u89d2\u8272\n"
            "\u6797\u7167\uff1a\u4eca\u665a\u4e0d\u80fd\u518d\u7b49\u4e86\u3002\n"
            "\u201c\u522b\u51fa\u58f0\u3002\u201d\u6c88\u5c9a\u4f4e\u58f0\u8bf4\u3002\n"
            "\u6c88\u5c9a\u62ac\u5934\uff0c\u770b\u89c1\u540e\u53f0\u95e8\u7f1d\u91cc\u7684\u51b7\u5149\u3002\n"
            "\u6797\u7167\uff1a\u8ddf\u6211\u8d70\u3002\n"
        )

        characters = extract_character_table(text)
        by_name = {character["name"]: character for character in characters}

        self.assertEqual(characters[0]["name"], "\u6797\u7167")
        self.assertIn("\u6c88\u5c9a", by_name)
        self.assertNotIn("\u6807\u9898", by_name)
        self.assertEqual(by_name["\u6797\u7167"]["role"], "\u4e3b\u8981\u89d2\u8272")
        self.assertIn("\u5bf9\u8bdd\u6807\u8bb0", by_name["\u6797\u7167"]["description"])
        self.assertIn("\u5bf9\u8bdd\u5f52\u56e0", by_name["\u6c88\u5c9a"]["description"])
        self.assertIn("\u53d9\u8ff0\u52a8\u4f5c", by_name["\u6c88\u5c9a"]["description"])

    def test_filters_metadata_colon_labels(self) -> None:
        text = (
            "\u65f6\u95f4\uff1a\u6df1\u591c\n"
            "\u5730\u70b9\uff1a\u65e7\u620f\u9662\n"
            "\u5907\u6ce8\uff1a\u706f\u5149\u5f88\u6697\n"
            "\u6797\u7167\uff1a\u95e8\u540e\u6709\u4eba\u3002\n"
        )

        names = [character["name"] for character in extract_character_table(text)]

        self.assertEqual(names, ["\u6797\u7167"])

    def test_extracts_inline_speaker_after_metadata_labels(self) -> None:
        text = "\u65f6\u95f4\uff1a\u3001\u5730\u70b9\uff1a\u3001\u6797\u7167\uff1a\u5bf9\u767d"

        names = [character["name"] for character in extract_character_table(text)]

        self.assertEqual(names, ["\u6797\u7167"])

    def test_filters_object_labels_and_embedded_action_phrases(self) -> None:
        text = (
            "\u6797\u7167\uff1a\u706f\u5854\u4e0d\u8be5\u505c\u3002\n"
            "\u5979\u5728\u706f\u5854\u95e8\u53e3\u6361\u5230\u4e00\u5f20\u65e7\u8239\u7968\uff0c"
            "\u80cc\u9762\u5199\u7740\uff1a\u522b\u76f8\u4fe1\u6f6e\u6c50\u8868\u3002\n"
            "\u6797\u7167\u542f\u52a8\u5907\u7528\u706f\uff0c\u6d77\u9762\u4e0a\u7684\u641c\u6551\u8239\u7ec8\u4e8e\u770b\u89c1\u706f\u5149\u3002\n"
        )

        names = [character["name"] for character in extract_character_table(text)]

        self.assertEqual(names, ["\u6797\u7167"])
        self.assertNotIn("\u80cc\u9762\u5199\u7740", names)
        self.assertNotIn("\u6551\u8239\u7ec8\u4e8e", names)


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

    def test_skips_epub_front_and_back_matter(self) -> None:
        copyright_page = FakeEpubItem(
            "copyright",
            "item1.xhtml",
            "<html><body><p>版权信息</p><p>书名：且听风吟（2023修订版）</p><p>作者：村上春树</p></body></html>",
        )
        digital_lab = FakeEpubItem(
            "intro",
            "item2.xhtml",
            "<html><body><p>Digital Lab是上海译文出版社数字业务的实验部门。</p><p>上海译文出版社｜Digital Lab</p></body></html>",
        )
        translator_preface = FakeEpubItem(
            "preface",
            "item3.xhtml",
            "<html><body><p>一切都将一去杳然（译序）</p><p>林少华</p><p>这部小说是村上春树的处女作。</p></body></html>",
        )
        first = FakeEpubItem(
            "story-1",
            "item4.xhtml",
            "<html><body><p>且听风吟</p><p>1</p><p>“不存在十全十美的文章。”</p></body></html>",
        )
        second = FakeEpubItem(
            "story-2",
            "item5.xhtml",
            "<html><body><p>2</p><p>故事从一九七〇年八月八日开始。</p></body></html>",
        )
        chronology = FakeEpubItem(
            "chronology",
            "item6.xhtml",
            "<html><body><p>村上春树年谱</p><p>1949年 1月12日出生。</p></body></html>",
        )
        music = FakeEpubItem(
            "music",
            "item7.xhtml",
            "<html><body><p>《且听风吟》音乐列表</p><p>California Girls</p></body></html>",
        )
        items = [copyright_page, digital_lab, translator_preface, first, second, chronology, music]
        book = FakeEpubBook(
            items=items,
            spine=[(item.get_id(), "yes") for item in items],
        )

        with patch("converter.services.epub_parser.epub.read_epub", return_value=book):
            text = extract_epub_text(b"fake epub bytes")

        chapters = split_chapters(text)

        self.assertEqual(len(chapters), 2)
        self.assertEqual([chapter.title for chapter in chapters], ["第1章 EPUB 章节 1", "第2章 EPUB 章节 2"])
        self.assertIn("不存在十全十美", chapters[0].text)
        self.assertIn("一九七〇年", chapters[1].text)
        self.assertNotIn("版权信息", text)
        self.assertNotIn("译序", text)
        self.assertNotIn("年谱", text)
        self.assertNotIn("音乐列表", text)


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
    def test_chapter_prompt_includes_character_grounding(self) -> None:
        chapter = Chapter(index=1, title="\u7b2c\u4e00\u7ae0 \u96e8\u591c", text=SAMPLE_TEXT)
        characters = [
            {
                "name": "\u6797\u7167",
                "role": "\u4e3b\u8981\u89d2\u8272",
                "description": "\u539f\u6587\u8bc1\u636e\uff1a2 \u5904\u5bf9\u8bdd\u6807\u8bb0",
            }
        ]

        prompt = build_chapter_prompt(chapter, characters)

        self.assertIn("Grounding rules:", prompt)
        self.assertIn("Use only the provided chapter text", prompt)
        self.assertIn("\u80cc\u9762\u5199\u7740", prompt)
        self.assertIn("Known characters JSON", prompt)
        self.assertIn("\u6797\u7167", prompt)
        self.assertIn("<chapter_text>", prompt)

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

    def test_reorders_beats_to_match_source_chronology(self) -> None:
        chapter_text = (
            "\u7b2c\u4e09\u7ae0 \u6f6e\u6c50\u8868\n"
            "\u6797\u7167\u548c\u6c88\u5c9a\u53bb\u6863\u6848\u9986\uff0c"
            "\u53d1\u73b0\u8fc7\u53bb\u4e09\u4e2a\u6708\u7684\u6f6e\u6c50\u8868\u90fd\u88ab\u4eba\u6539\u8fc7\u3002\n"
            "\u65e7\u7ba1\u7406\u5458\u544a\u8bc9\u5979\u4eec\uff0c"
            "\u5341\u5e74\u524d\u6709\u4e00\u8258\u8d27\u8239\u5728\u706f\u5854\u5916\u6c89\u6ca1\uff0c"
            "\u4f46\u4e8b\u6545\u62a5\u544a\u4ece\u672a\u516c\u5f00\u3002\n"
            "\u6c88\u5c9a\uff1a\u6709\u4eba\u4e00\u76f4\u5728\u8ba9\u8239\u9760\u9519\u65b9\u5411\u3002\n"
        )
        client = FakeClaudeClient(
            """
            {
              "title": "\u6f6e\u6c50\u8868",
              "summary": "\u6863\u6848\u9986\u91cc\u7684\u8bb0\u5f55\u6307\u5411\u65e7\u6848\u3002",
              "beats": [
                {"type": "direction", "content": "\u7279\u5199\uff1a\u4e09\u4efd\u6f6e\u6c50\u8868\u5e76\u6392\u644a\u5f00\u3002"},
                {"type": "dialogue", "character": "\u6c88\u5c9a", "content": "\u6709\u4eba\u4e00\u76f4\u5728\u8ba9\u8239\u9760\u9519\u65b9\u5411\u3002"},
                {"type": "action", "content": "\u65e7\u7ba1\u7406\u5458\u501a\u5728\u95e8\u8fb9\uff0c\u8896\u53e3\u78e8\u5f97\u53d1\u4eae\u3002"},
                {"type": "dialogue", "character": "\u65e7\u7ba1\u7406\u5458", "content": "\u5341\u5e74\u524d\uff0c\u4e00\u8258\u8d27\u8239\u5728\u706f\u5854\u5916\u6c89\u4e86\u3002\u4e8b\u6545\u62a5\u544a\u6ca1\u516c\u5f00\u8fc7\u3002"}
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

        scene = converter.convert_chapter(
            Chapter(index=3, title="\u7b2c\u4e09\u7ae0 \u6f6e\u6c50\u8868", text=chapter_text),
            [
                {"name": "\u6c88\u5c9a", "role": "\u4e3b\u8981\u89d2\u8272"},
                {"name": "\u65e7\u7ba1\u7406\u5458", "role": "\u914d\u89d2"},
            ],
        )

        contents = [beat["content"] for beat in scene["beats"]]
        self.assertEqual(
            contents,
            [
                "\u7279\u5199\uff1a\u4e09\u4efd\u6f6e\u6c50\u8868\u5e76\u6392\u644a\u5f00\u3002",
                "\u65e7\u7ba1\u7406\u5458\u501a\u5728\u95e8\u8fb9\uff0c\u8896\u53e3\u78e8\u5f97\u53d1\u4eae\u3002",
                "\u5341\u5e74\u524d\uff0c\u4e00\u8258\u8d27\u8239\u5728\u706f\u5854\u5916\u6c89\u4e86\u3002\u4e8b\u6545\u62a5\u544a\u6ca1\u516c\u5f00\u8fc7\u3002",
                "\u6709\u4eba\u4e00\u76f4\u5728\u8ba9\u8239\u9760\u9519\u65b9\u5411\u3002",
            ],
        )

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
    def test_health_check_endpoint_returns_ok(self) -> None:
        response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_health_check_skips_https_redirect(self) -> None:
        response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @override_settings(
        LLM_PROVIDER="auto",
        ANTHROPIC_API_KEY="",
        OPENAI_API_KEY="",
        QWEN_API_KEY="",
    )
    def test_convert_text_returns_task_before_background_conversion_finishes(self) -> None:
        with patch("converter.views.start_conversion_task") as start_task:
            created = self.client.post("/api/convert", {"text": SAMPLE_TEXT})

        self.assertEqual(created.status_code, 201)
        task_id = created.json()["task_id"]
        task = ConversionTask.objects.get(id=task_id)
        start_task.assert_called_once_with(task)

        status_response = self.client.get(f"/api/status/{task_id}")

        self.assertEqual(status_response.json()["status"], "pending")
        self.assertEqual(status_response.json()["llm_provider"], "placeholder")
        self.assertEqual(status_response.json()["input_name"], "pasted-text.txt")

    def test_background_runner_sanitizes_provider_auth_error(self) -> None:
        raw_error = (
            "Error code: 401 - {'error': {'message': 'Incorrect API key provided: "
            "sk_a79fb********************************52c8. You can find your API key at "
            "https://platform.openai.com/account/api-keys.', 'code': 'invalid_api_key'}}"
        )

        task = ConversionTask.objects.create(input_name="bad-key.txt", source_text=SAMPLE_TEXT)

        with patch("converter.services.task_runner.run_conversion_task", side_effect=Exception(raw_error)):
            from converter.services.task_runner import _run_and_capture_failure

            _run_and_capture_failure(task.id)

        status_response = self.client.get(f"/api/status/{task.id}")
        error_message = status_response.json()["error_message"]

        self.assertEqual(status_response.json()["status"], "failed")
        self.assertEqual(status_response.json()["progress"], 100)
        self.assertIn("OpenAI 连接凭据无效", error_message)
        self.assertIn("本地演示方式", error_message)
        self.assertNotIn("sk_a79fb", error_message)
        self.assertNotIn("platform.openai.com", error_message)
        self.assertNotIn("invalid_api_key", error_message)

    def test_background_runner_ignores_missing_task(self) -> None:
        from converter.services.task_runner import _run_and_capture_failure

        _run_and_capture_failure("00000000-0000-0000-0000-000000000000")

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

    @override_settings(
        LLM_PROVIDER="auto",
        ANTHROPIC_API_KEY="",
        OPENAI_API_KEY="",
        QWEN_API_KEY="",
    )
    def test_status_includes_chapter_previews_after_pipeline_starts(self) -> None:
        task = ConversionTask.objects.create(
            input_name="sample.txt",
            source_format=ConversionTask.SourceFormat.TEXT,
            source_text=SAMPLE_TEXT,
        )

        run_conversion_task(task)

        status_response = self.client.get(f"/api/status/{task.id}")
        payload = status_response.json()

        self.assertEqual(payload["status"], "completed")
        self.assertIs(payload["can_view_result"], True)
        self.assertEqual(payload["input_name"], "sample.txt")
        self.assertEqual(payload["source_format"], "text")
        self.assertEqual(payload["total_chapters"], 2)
        self.assertEqual(len(payload["chapters"]), 2)
        self.assertEqual(payload["chapters"][0]["title"], "\u7b2c\u4e00\u7ae0 \u96e8\u591c")
        self.assertIn("\u6797\u7167", payload["chapters"][0]["excerpt"])
        self.assertNotIn("text", payload["chapters"][0])

    def test_status_hides_result_entry_before_any_scene_is_ready(self) -> None:
        task = ConversionTask.objects.create(
            input_name="sample.txt",
            source_format=ConversionTask.SourceFormat.TEXT,
            source_text=SAMPLE_TEXT,
            status=ConversionTask.Status.PROCESSING,
        )

        status_response = self.client.get(f"/api/status/{task.id}")

        self.assertIs(status_response.json()["can_view_result"], False)


class ConversionPipelineTests(TestCase):
    def test_assemble_script_groups_three_or_more_scenes_into_acts(self) -> None:
        scenes = [
            scene_payload(number=99, source_chapter=1, title="\u96e8\u591c"),
            scene_payload(number=99, source_chapter=2, title="\u540e\u53f0"),
            scene_payload(number=99, source_chapter=3, title="\u51b7\u5149"),
            scene_payload(number=99, source_chapter=4, title="\u8ffd\u95ee"),
            scene_payload(number=99, source_chapter=5, title="\u771f\u76f8"),
        ]

        script = assemble_script(title="\u6837\u672c", characters=[], scenes=scenes)

        self.assertEqual([act["number"] for act in script["acts"]], [1, 2, 3])
        self.assertEqual(
            [act["title"] for act in script["acts"]],
            ["\u7b2c\u4e00\u5e55\uff1a\u5f00\u7aef", "\u7b2c\u4e8c\u5e55\uff1a\u5c55\u5f00", "\u7b2c\u4e09\u5e55\uff1a\u6536\u675f"],
        )
        self.assertEqual([len(act["scenes"]) for act in script["acts"]], [1, 3, 1])
        all_scenes = [scene for act in script["acts"] for scene in act["scenes"]]
        self.assertEqual([scene["number"] for scene in all_scenes], [1, 2, 3, 4, 5])
        self.assertEqual([scene["source_chapter"] for scene in all_scenes], [1, 2, 3, 4, 5])

    def test_assemble_script_keeps_short_scripts_in_one_act(self) -> None:
        script = assemble_script(
            title="\u6837\u672c",
            characters=[],
            scenes=[
                scene_payload(number=8, source_chapter=1, title="\u96e8\u591c"),
                scene_payload(number=9, source_chapter=2, title="\u540e\u53f0"),
            ],
        )

        self.assertEqual(len(script["acts"]), 1)
        self.assertEqual(script["acts"][0]["title"], "\u7b2c\u4e00\u5e55\uff1a\u5168\u7bc7")
        self.assertEqual([scene["number"] for scene in script["acts"][0]["scenes"]], [1, 2])

    def test_assemble_script_uses_valid_act_boundaries(self) -> None:
        scenes = [
            scene_payload(number=99, source_chapter=1, title="\u96e8\u591c"),
            scene_payload(number=99, source_chapter=2, title="\u540e\u53f0"),
            scene_payload(number=99, source_chapter=3, title="\u51b7\u5149"),
            scene_payload(number=99, source_chapter=4, title="\u8ffd\u95ee"),
            scene_payload(number=99, source_chapter=5, title="\u771f\u76f8"),
        ]
        boundaries = [
            ActBoundary(1, "\u7b2c\u4e00\u5e55\uff1a\u5f00\u7aef", 1, 2),
            ActBoundary(2, "\u7b2c\u4e8c\u5e55\uff1a\u5c55\u5f00", 3, 4),
            ActBoundary(3, "\u7b2c\u4e09\u5e55\uff1a\u6536\u675f", 5, 5),
        ]

        script = assemble_script(title="\u6837\u672c", characters=[], scenes=scenes, act_boundaries=boundaries)

        self.assertEqual([len(act["scenes"]) for act in script["acts"]], [2, 2, 1])
        self.assertEqual(
            [scene["number"] for act in script["acts"] for scene in act["scenes"]],
            [1, 2, 3, 4, 5],
        )

    def test_assemble_script_falls_back_for_invalid_act_boundaries(self) -> None:
        scenes = [
            scene_payload(number=99, source_chapter=1, title="\u96e8\u591c"),
            scene_payload(number=99, source_chapter=2, title="\u540e\u53f0"),
            scene_payload(number=99, source_chapter=3, title="\u51b7\u5149"),
            scene_payload(number=99, source_chapter=4, title="\u8ffd\u95ee"),
            scene_payload(number=99, source_chapter=5, title="\u771f\u76f8"),
        ]
        boundaries = [
            ActBoundary(1, "\u7b2c\u4e00\u5e55\uff1a\u5f00\u7aef", 1, 1),
            ActBoundary(2, "\u7b2c\u4e8c\u5e55\uff1a\u5c55\u5f00", 3, 4),
            ActBoundary(3, "\u7b2c\u4e09\u5e55\uff1a\u6536\u675f", 5, 5),
        ]

        script = assemble_script(title="\u6837\u672c", characters=[], scenes=scenes, act_boundaries=boundaries)

        self.assertEqual([len(act["scenes"]) for act in script["acts"]], [1, 3, 1])

    def test_partial_script_uses_single_processed_section(self) -> None:
        scenes = [
            scene_payload(number=99, source_chapter=1, title="\u96e8\u591c"),
            scene_payload(number=99, source_chapter=2, title="\u540e\u53f0"),
            scene_payload(number=99, source_chapter=3, title="\u51b7\u5149"),
            scene_payload(number=99, source_chapter=4, title="\u8ffd\u95ee"),
            scene_payload(number=99, source_chapter=5, title="\u771f\u76f8"),
        ]

        script = assemble_partial_script(title="\u6837\u672c", characters=[], scenes=scenes)

        self.assertEqual(len(script["acts"]), 1)
        self.assertEqual(script["acts"][0]["title"], "\u5df2\u5904\u7406\u90e8\u5206")
        self.assertEqual([scene["number"] for scene in script["acts"][0]["scenes"]], [1, 2, 3, 4, 5])

    def test_normalize_act_boundary_payload_requires_full_scene_coverage(self) -> None:
        payload = {
            "acts": [
                {"number": 1, "start_scene": 1, "end_scene": 1, "rationale": "\u5f00\u573a"},
                {"number": 2, "start_scene": 3, "end_scene": 4, "rationale": "\u53d1\u5c55"},
                {"number": 3, "start_scene": 5, "end_scene": 5, "rationale": "\u6536\u675f"},
            ]
        }

        with self.assertRaisesMessage(Exception, "cover every scene"):
            normalize_act_boundary_payload(payload, scene_count=5)

    def test_act_boundary_prompt_includes_scene_events(self) -> None:
        prompt = build_act_boundary_prompt(
            [
                {
                    "number": 1,
                    "source_chapter": 2,
                    "title": "\u540e\u53f0",
                    "summary": "\u6c88\u5c9a\u542c\u89c1\u5f02\u54cd\u3002",
                    "beats": [
                        {
                            "type": "dialogue",
                            "character": "\u6c88\u5c9a",
                            "content": "\u4f60\u542c\u89c1\u4e86\u5417\uff1f",
                        }
                    ],
                }
            ]
        )

        self.assertIn('"source_chapter": 2', prompt)
        self.assertIn("\u6c88\u5c9a", prompt)
        self.assertIn("\u4f60\u542c\u89c1\u4e86\u5417", prompt)

    def test_placeholder_filters_metadata_dialogue_with_character_table(self) -> None:
        converter = PlaceholderSceneConverter()
        chapter = Chapter(
            index=1,
            title="\u5168\u6587",
            text="\u65f6\u95f4\uff1a\u6df1\u591c\n\u6797\u7167\uff1a\u95e8\u540e\u6709\u4eba\u3002",
        )

        scene = converter.convert_chapter(
            chapter,
            [{"name": "\u6797\u7167", "role": "\u5bf9\u8bdd\u89d2\u8272"}],
        )

        self.assertEqual(scene["beats"][0]["type"], "action")
        self.assertEqual(scene["beats"][1]["type"], "dialogue")
        self.assertEqual(scene["beats"][1]["character"], "\u6797\u7167")

    def test_placeholder_does_not_treat_metadata_as_dialogue_without_character_table(self) -> None:
        converter = PlaceholderSceneConverter()
        chapter = Chapter(index=1, title="\u5168\u6587", text="\u65f6\u95f4\uff1a\u6df1\u591c")

        scene = converter.convert_chapter(chapter, [])

        self.assertEqual(scene["beats"], [{"type": "action", "content": "\u65f6\u95f4\uff1a\u6df1\u591c"}])

    def test_placeholder_extracts_dialogue_from_inline_metadata_and_speaker(self) -> None:
        converter = PlaceholderSceneConverter()
        chapter = Chapter(
            index=1,
            title="\u5168\u6587",
            text="\u65f6\u95f4\uff1a\u3001\u5730\u70b9\uff1a\u3001\u6797\u7167\uff1a\u5bf9\u767d",
        )

        scene = converter.convert_chapter(
            chapter,
            [{"name": "\u6797\u7167", "role": "\u5bf9\u8bdd\u89d2\u8272"}],
        )

        self.assertEqual(scene["beats"], [{"type": "dialogue", "character": "\u6797\u7167", "content": "\u5bf9\u767d"}])

    def test_placeholder_turns_chinese_attributed_quote_into_dialogue(self) -> None:
        converter = PlaceholderSceneConverter()
        chapter = Chapter(index=1, title="\u5168\u6587", text="\u201c\u522b\u51fa\u58f0\u3002\u201d\u6c88\u5c9a\u4f4e\u58f0\u8bf4\u3002")

        scene = converter.convert_chapter(
            chapter,
            [{"name": "\u6c88\u5c9a", "role": "\u53d9\u8ff0\u63d0\u53ca\u89d2\u8272"}],
        )

        self.assertEqual(
            scene["beats"],
            [
                {
                    "type": "dialogue",
                    "character": "\u6c88\u5c9a",
                    "content": "\u522b\u51fa\u58f0\u3002",
                    "parenthetical": "\u4f4e\u58f0",
                }
            ],
        )

    @override_settings(
        LLM_PROVIDER="placeholder",
        ANTHROPIC_API_KEY="real-looking-key",
        OPENAI_API_KEY="real-looking-key",
        QWEN_API_KEY="real-looking-key",
    )
    def test_placeholder_provider_never_uses_external_keys(self) -> None:
        converter = build_scene_converter()

        self.assertEqual(converter.__class__.__name__, "PlaceholderSceneConverter")

    @override_settings(LLM_PROVIDER="placeholder")
    def test_placeholder_provider_does_not_build_act_boundary_planner(self) -> None:
        self.assertIsNone(build_act_boundary_planner("placeholder"))

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
        passed_characters = converter.convert_chapter.call_args_list[0].args[1]
        self.assertEqual(passed_characters[0]["name"], "\u6797\u7167")
        self.assertIn("\u539f\u6587\u8bc1\u636e", passed_characters[0]["description"])
        self.assertEqual(task.status, "completed")
        self.assertEqual(task.chapters_done, 2)
        script = yaml.safe_load(task.script_yaml)
        self.assertEqual(script["acts"][0]["title"], "\u7b2c\u4e00\u5e55\uff1a\u5168\u7bc7")
        self.assertEqual([scene["number"] for scene in script["acts"][0]["scenes"]], [1, 2])
        self.assertEqual(script["acts"][0]["scenes"][0]["title"], "\u96e8\u591c\u5bf9\u5cd9")

    @override_settings(
        ANTHROPIC_API_KEY="test-key",
        OPENAI_API_KEY="",
        QWEN_API_KEY="",
        LLM_PROVIDER="anthropic",
        ANTHROPIC_MODEL="claude-test",
        LLM_MAX_TOKENS=1000,
    )
    def test_pipeline_persists_partial_script_after_each_chapter(self) -> None:
        task = ConversionTask.objects.create(
            input_name="partial.txt",
            source_text=SAMPLE_TEXT,
        )
        observed: dict[str, object] = {}

        def convert_side_effect(chapter, characters):  # noqa: ANN001, ARG001
            if chapter.index == 1:
                return scene_payload(number=1, source_chapter=1, title="\u96e8\u591c")

            task.refresh_from_db()
            observed["status"] = task.status
            observed["chapters_done"] = task.chapters_done
            observed["progress"] = task.progress
            observed["script"] = yaml.safe_load(task.script_yaml)
            return scene_payload(number=2, source_chapter=2, title="\u540e\u53f0")

        with patch("converter.services.pipeline.ClaudeSceneConverter") as converter_class:
            converter = converter_class.return_value
            converter.convert_chapter.side_effect = convert_side_effect

            run_conversion_task(task)

        partial_script = observed["script"]
        partial_scenes = [scene for act in partial_script["acts"] for scene in act["scenes"]]
        self.assertEqual(observed["status"], ConversionTask.Status.PROCESSING)
        self.assertEqual(observed["chapters_done"], 1)
        self.assertGreater(observed["progress"], 25)
        self.assertEqual([act["title"] for act in partial_script["acts"]], ["\u5df2\u5904\u7406\u90e8\u5206"])
        self.assertEqual([scene["title"] for scene in partial_scenes], ["\u96e8\u591c"])

        task.refresh_from_db()
        self.assertEqual(task.status, ConversionTask.Status.COMPLETED)

    @override_settings(
        LLM_PROVIDER="anthropic",
        ANTHROPIC_API_KEY="test-key",
        OPENAI_API_KEY="",
        QWEN_API_KEY="",
        ANTHROPIC_MODEL="claude-test",
        LLM_MAX_TOKENS=1000,
        LLM_SCENE_MAX_ATTEMPTS=2,
    )
    def test_pipeline_retries_failed_chapter_conversion(self) -> None:
        task = ConversionTask.objects.create(
            input_name="retry.txt",
            source_text=SAMPLE_TEXT,
        )

        with patch("converter.services.pipeline.ClaudeSceneConverter") as converter_class:
            converter = converter_class.return_value
            converter.convert_chapter.side_effect = [
                SceneConversionError("LLM response was not valid JSON."),
                scene_payload(number=1, source_chapter=1, title="\u96e8\u591c\u91cd\u8bd5\u6210\u529f"),
                scene_payload(number=2, source_chapter=2, title="\u540e\u53f0"),
            ]

            run_conversion_task(task)

        task.refresh_from_db()
        self.assertEqual(converter.convert_chapter.call_count, 3)
        self.assertEqual(task.status, ConversionTask.Status.COMPLETED)
        self.assertEqual(task.error_message, "")
        script = yaml.safe_load(task.script_yaml)
        self.assertEqual(script["acts"][0]["scenes"][0]["title"], "\u96e8\u591c\u91cd\u8bd5\u6210\u529f")

    @override_settings(
        LLM_PROVIDER="anthropic",
        ANTHROPIC_API_KEY="test-key",
        OPENAI_API_KEY="",
        QWEN_API_KEY="",
        ANTHROPIC_MODEL="claude-test",
        LLM_MAX_TOKENS=1000,
        LLM_SCENE_MAX_ATTEMPTS=2,
    )
    def test_pipeline_marks_chapter_for_manual_review_after_retry_exhaustion(self) -> None:
        task = ConversionTask.objects.create(
            input_name="manual-review.txt",
            source_text=SAMPLE_TEXT,
        )

        with patch("converter.services.pipeline.ClaudeSceneConverter") as converter_class:
            converter = converter_class.return_value
            converter.convert_chapter.side_effect = [
                SceneConversionError("LLM response was not valid JSON."),
                SceneConversionError("LLM scene must include at least one beat."),
                scene_payload(number=2, source_chapter=2, title="\u540e\u53f0"),
            ]

            run_conversion_task(task)

        task.refresh_from_db()
        self.assertEqual(converter.convert_chapter.call_count, 3)
        self.assertEqual(task.status, ConversionTask.Status.COMPLETED)
        self.assertEqual(task.chapters_done, 2)
        self.assertIn("\u9700\u4eba\u5de5\u5904\u7406", task.error_message)
        script = yaml.safe_load(task.script_yaml)
        scenes = [scene for act in script["acts"] for scene in act["scenes"]]
        self.assertEqual(scenes[0]["source_chapter"], 1)
        self.assertIn("\u9700\u4eba\u5de5\u5904\u7406", scenes[0]["title"])
        self.assertEqual(scenes[0]["beats"][0]["type"], "direction")
        self.assertIn("\u8bf7\u53c2\u8003\u5de6\u4fa7\u539f\u6587", scenes[0]["beats"][0]["content"])
        self.assertEqual(scenes[1]["title"], "\u540e\u53f0")

    @override_settings(
        LLM_PROVIDER="anthropic",
        ANTHROPIC_API_KEY="test-key",
        OPENAI_API_KEY="",
        QWEN_API_KEY="",
        ANTHROPIC_MODEL="claude-test",
        LLM_MAX_TOKENS=1000,
        LLM_SCENE_MAX_ATTEMPTS=2,
    )
    def test_pipeline_does_not_retry_provider_auth_errors(self) -> None:
        task = ConversionTask.objects.create(
            input_name="auth-error.txt",
            source_text=SAMPLE_TEXT,
        )
        raw_error = "Error code: 401 - invalid_api_key: Incorrect API key provided."

        with patch("converter.services.pipeline.ClaudeSceneConverter") as converter_class:
            converter = converter_class.return_value
            converter.convert_chapter.side_effect = Exception(raw_error)

            with self.assertRaisesMessage(Exception, "invalid_api_key"):
                run_conversion_task(task)

        self.assertEqual(converter.convert_chapter.call_count, 1)

    @override_settings(
        LLM_PROVIDER="anthropic",
        ANTHROPIC_API_KEY="test-key",
        OPENAI_API_KEY="",
        QWEN_API_KEY="",
        ANTHROPIC_MODEL="claude-test",
        LLM_MAX_TOKENS=1000,
    )
    def test_pipeline_persists_multi_act_script_for_three_or_more_chapters(self) -> None:
        source_text = (
            "\u7b2c\u4e00\u7ae0 \u96e8\u591c\n\u6797\u7167\uff1a\u5f00\u95e8\u3002\n\n"
            "\u7b2c\u4e8c\u7ae0 \u540e\u53f0\n\u6c88\u5c9a\uff1a\u542c\u89c1\u4e86\u5417\uff1f\n\n"
            "\u7b2c\u4e09\u7ae0 \u51b7\u5149\n\u706f\u5149\u4ece\u95e8\u7f1d\u91cc\u900f\u51fa\u3002\n"
        )
        task = ConversionTask.objects.create(input_name="three.txt", source_text=source_text)

        with (
            patch("converter.services.pipeline.ClaudeSceneConverter") as converter_class,
            patch("converter.services.pipeline.build_act_boundary_planner", return_value=None),
        ):
            converter = converter_class.return_value
            converter.convert_chapter.side_effect = [
                scene_payload(number=10, source_chapter=1, title="\u96e8\u591c"),
                scene_payload(number=10, source_chapter=2, title="\u540e\u53f0"),
                scene_payload(number=10, source_chapter=3, title="\u51b7\u5149"),
            ]

            run_conversion_task(task)

        task.refresh_from_db()
        self.assertEqual(task.status, "completed")
        script = yaml.safe_load(task.script_yaml)
        self.assertEqual(
            [act["title"] for act in script["acts"]],
            ["\u7b2c\u4e00\u5e55\uff1a\u5f00\u7aef", "\u7b2c\u4e8c\u5e55\uff1a\u5c55\u5f00", "\u7b2c\u4e09\u5e55\uff1a\u6536\u675f"],
        )
        all_scenes = [scene for act in script["acts"] for scene in act["scenes"]]
        self.assertEqual([scene["number"] for scene in all_scenes], [1, 2, 3])
        self.assertEqual([scene["source_chapter"] for scene in all_scenes], [1, 2, 3])

    @override_settings(
        LLM_PROVIDER="anthropic",
        ANTHROPIC_API_KEY="test-key",
        OPENAI_API_KEY="",
        QWEN_API_KEY="",
        ANTHROPIC_MODEL="claude-test",
        LLM_MAX_TOKENS=1000,
    )
    def test_pipeline_uses_model_act_boundaries_for_final_script(self) -> None:
        source_text = (
            "\u7b2c\u4e00\u7ae0 \u96e8\u591c\n\u6797\u7167\uff1a\u5f00\u95e8\u3002\n\n"
            "\u7b2c\u4e8c\u7ae0 \u540e\u53f0\n\u6c88\u5c9a\uff1a\u542c\u89c1\u4e86\u5417\uff1f\n\n"
            "\u7b2c\u4e09\u7ae0 \u51b7\u5149\n\u706f\u5149\u4ece\u95e8\u7f1d\u91cc\u900f\u51fa\u3002\n\n"
            "\u7b2c\u56db\u7ae0 \u771f\u76f8\n\u95e8\u6253\u5f00\u4e86\u3002\n"
        )
        task = ConversionTask.objects.create(input_name="four.txt", source_text=source_text)
        planner = FakeActBoundaryPlanner(
            [
                ActBoundary(1, "\u7b2c\u4e00\u5e55\uff1a\u5f00\u7aef", 1, 2),
                ActBoundary(2, "\u7b2c\u4e8c\u5e55\uff1a\u5c55\u5f00", 3, 3),
                ActBoundary(3, "\u7b2c\u4e09\u5e55\uff1a\u6536\u675f", 4, 4),
            ]
        )

        with (
            patch("converter.services.pipeline.ClaudeSceneConverter") as converter_class,
            patch("converter.services.pipeline.build_act_boundary_planner", return_value=planner),
        ):
            converter = converter_class.return_value
            converter.convert_chapter.side_effect = [
                scene_payload(number=10, source_chapter=1, title="\u96e8\u591c"),
                scene_payload(number=10, source_chapter=2, title="\u540e\u53f0"),
                scene_payload(number=10, source_chapter=3, title="\u51b7\u5149"),
                scene_payload(number=10, source_chapter=4, title="\u771f\u76f8"),
            ]

            run_conversion_task(task)

        task.refresh_from_db()
        script = yaml.safe_load(task.script_yaml)
        self.assertEqual([len(act["scenes"]) for act in script["acts"]], [2, 1, 1])
        self.assertEqual(planner.seen_scene_numbers, [1, 2, 3, 4])

    @override_settings(
        LLM_PROVIDER="anthropic",
        ANTHROPIC_API_KEY="test-key",
        OPENAI_API_KEY="",
        QWEN_API_KEY="",
        ANTHROPIC_MODEL="claude-test",
        LLM_MAX_TOKENS=1000,
    )
    def test_pipeline_falls_back_when_model_act_boundaries_are_invalid(self) -> None:
        source_text = (
            "\u7b2c\u4e00\u7ae0 \u96e8\u591c\n\u6797\u7167\uff1a\u5f00\u95e8\u3002\n\n"
            "\u7b2c\u4e8c\u7ae0 \u540e\u53f0\n\u6c88\u5c9a\uff1a\u542c\u89c1\u4e86\u5417\uff1f\n\n"
            "\u7b2c\u4e09\u7ae0 \u51b7\u5149\n\u706f\u5149\u4ece\u95e8\u7f1d\u91cc\u900f\u51fa\u3002\n\n"
            "\u7b2c\u56db\u7ae0 \u771f\u76f8\n\u95e8\u6253\u5f00\u4e86\u3002\n"
        )
        task = ConversionTask.objects.create(input_name="fallback.txt", source_text=source_text)
        planner = FakeActBoundaryPlanner(
            [
                ActBoundary(1, "\u7b2c\u4e00\u5e55\uff1a\u5f00\u7aef", 1, 2),
                ActBoundary(2, "\u7b2c\u4e8c\u5e55\uff1a\u5c55\u5f00", 2, 3),
                ActBoundary(3, "\u7b2c\u4e09\u5e55\uff1a\u6536\u675f", 4, 4),
            ]
        )

        with (
            patch("converter.services.pipeline.ClaudeSceneConverter") as converter_class,
            patch("converter.services.pipeline.build_act_boundary_planner", return_value=planner),
        ):
            converter = converter_class.return_value
            converter.convert_chapter.side_effect = [
                scene_payload(number=10, source_chapter=1, title="\u96e8\u591c"),
                scene_payload(number=10, source_chapter=2, title="\u540e\u53f0"),
                scene_payload(number=10, source_chapter=3, title="\u51b7\u5149"),
                scene_payload(number=10, source_chapter=4, title="\u771f\u76f8"),
            ]

            run_conversion_task(task)

        task.refresh_from_db()
        script = yaml.safe_load(task.script_yaml)
        self.assertEqual([len(act["scenes"]) for act in script["acts"]], [1, 2, 1])

    @override_settings(
        LLM_PROVIDER="anthropic",
        ANTHROPIC_API_KEY="test-key",
        OPENAI_API_KEY="",
        QWEN_API_KEY="",
        ANTHROPIC_MODEL="claude-test",
        LLM_MAX_TOKENS=1000,
    )
    def test_pipeline_falls_back_when_act_boundary_planner_is_unavailable(self) -> None:
        source_text = (
            "\u7b2c\u4e00\u7ae0 \u96e8\u591c\n\u6797\u7167\uff1a\u5f00\u95e8\u3002\n\n"
            "\u7b2c\u4e8c\u7ae0 \u540e\u53f0\n\u6c88\u5c9a\uff1a\u542c\u89c1\u4e86\u5417\uff1f\n\n"
            "\u7b2c\u4e09\u7ae0 \u51b7\u5149\n\u706f\u5149\u4ece\u95e8\u7f1d\u91cc\u900f\u51fa\u3002\n\n"
            "\u7b2c\u56db\u7ae0 \u771f\u76f8\n\u95e8\u6253\u5f00\u4e86\u3002\n"
        )
        task = ConversionTask.objects.create(input_name="unavailable.txt", source_text=source_text)

        with (
            patch("converter.services.pipeline.ClaudeSceneConverter") as converter_class,
            patch("converter.services.pipeline.build_act_boundary_planner", side_effect=RuntimeError("timeout")),
        ):
            converter = converter_class.return_value
            converter.convert_chapter.side_effect = [
                scene_payload(number=10, source_chapter=1, title="\u96e8\u591c"),
                scene_payload(number=10, source_chapter=2, title="\u540e\u53f0"),
                scene_payload(number=10, source_chapter=3, title="\u51b7\u5149"),
                scene_payload(number=10, source_chapter=4, title="\u771f\u76f8"),
            ]

            run_conversion_task(task)

        task.refresh_from_db()
        self.assertEqual(task.status, ConversionTask.Status.COMPLETED)
        script = yaml.safe_load(task.script_yaml)
        self.assertEqual([len(act["scenes"]) for act in script["acts"]], [1, 2, 1])

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


class FakeActBoundaryPlanner:
    def __init__(self, boundaries: list[ActBoundary]) -> None:
        self.boundaries = boundaries
        self.seen_scene_numbers: list[int] = []

    def propose_boundaries(self, scenes: list[dict[str, object]]) -> list[ActBoundary]:
        self.seen_scene_numbers = [int(scene["number"]) for scene in scenes]
        return self.boundaries


def scene_payload(number: int, source_chapter: int, title: str) -> dict[str, object]:
    return {
        "number": number,
        "title": title,
        "source_chapter": source_chapter,
        "summary": f"{title}\u6458\u8981",
        "beats": [{"type": "action", "content": f"{title}\u53d1\u751f\u3002"}],
    }
