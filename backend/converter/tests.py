from django.test import TestCase, override_settings

from converter.services.chapter_splitter import split_chapters


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


class ConversionApiTests(TestCase):
    @override_settings(ANTHROPIC_API_KEY="")
    def test_convert_text_uses_placeholder_generator_without_api_key(self) -> None:
        created = self.client.post("/api/convert", {"text": SAMPLE_TEXT})

        self.assertEqual(created.status_code, 201)
        task_id = created.json()["task_id"]
        status_response = self.client.get(f"/api/status/{task_id}")
        result_response = self.client.get(f"/api/result/{task_id}")

        self.assertEqual(status_response.json()["status"], "completed")
        result = result_response.json()
        self.assertEqual(result["status"], "completed")
        self.assertIn("script_yaml", result)
        self.assertEqual(result["characters"][0]["name"], "\u6797\u7167")
