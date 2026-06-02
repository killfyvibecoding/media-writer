import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "make_xiaohongshu_post.py"
SPEC = importlib.util.spec_from_file_location("make_xiaohongshu_post", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class XiaohongshuPostTests(unittest.TestCase):
    def test_normalize_tags_adds_hash_and_deduplicates(self):
        tags = MODULE.normalize_tags(["AI工具", "#AI工具", " 内容创作 ", ""])

        self.assertEqual(tags, ["#AI工具", "#内容创作"])

    def test_write_outputs_markdown_and_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            markdown = Path(temp_dir) / "post.md"
            data_json = Path(temp_dir) / "post.json"

            MODULE.write_post(
                markdown_path=markdown,
                json_path=data_json,
                titles=["普通人做AI内容，别再只卷技术了"],
                hook="拆了100条爆款后，我发现真正让人转发的不是模型，而是情绪。",
                body_sections=[
                    ("先说结论", ["AI只是外壳，情绪才是发动机。"]),
                    ("怎么用", ["先找用户情绪，再决定用什么工具。"]),
                ],
                tags=["AI内容", "小红书运营", "#内容创作", "爆款笔记", "自媒体"],
                cover_suggestion="封面写：AI爆款不是技术，是情绪",
                source="source.md",
            )

            text = markdown.read_text(encoding="utf-8")
            data = data_json.read_text(encoding="utf-8")
            self.assertIn('post_type: "科普帖"', text)
            self.assertIn("帖子类型：科普帖", text)
            self.assertIn("标题候选", text)
            self.assertIn("#AI内容 #小红书运营 #内容创作 #爆款笔记 #自媒体", text)
            self.assertIn("封面建议", text)
            self.assertIn('"post_type": "科普帖"', data)
            self.assertIn('"tags"', data)


if __name__ == "__main__":
    unittest.main()
