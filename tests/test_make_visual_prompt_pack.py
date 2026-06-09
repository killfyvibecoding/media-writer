import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "make_visual_prompt_pack.py"
SPEC = importlib.util.spec_from_file_location("make_visual_prompt_pack", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class VisualPromptPackTests(unittest.TestCase):
    def test_write_prompt_pack_from_diagnosis(self):
        diagnosis = {
            "type": "content_diagnosis",
            "topic": "GPU之后，AI开始拼连接",
            "source": "source.md",
            "core_insight": "AI数据中心的下一轮竞争是连接效率。",
            "cognitive_gap": "大众只看GPU，忽略GPU之间怎么连。",
            "rewrite_angle": "从算力瓶颈转向连接瓶颈。",
            "visual_strategy": {
                "fit_score": 9,
                "explosive_potential": "GPU与连接瓶颈的认知反差强。",
                "logic_check": "可用机柜网络和堵车隐喻解释。",
                "audience_hook": "别只盯GPU。",
                "style_keywords": ["科技", "系统", "冷静"],
                "metaphors": ["GPU机柜网络", "高速路堵车"],
                "avoid": ["股票K线"],
                "asset_suggestions": [],
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            diagnosis_json = root / "diagnosis.json"
            diagnosis_json.write_text(json.dumps(diagnosis, ensure_ascii=False), encoding="utf-8")
            markdown = root / "visual.md"
            data_json = root / "visual.json"

            MODULE.write_prompt_pack(
                diagnosis_json=diagnosis_json,
                output_dir=root,
                stem="ai_connect",
                assets=["wechat-cover", "podcast-cover", "xiaohongshu-cover"],
                markdown_path=markdown,
                json_path=data_json,
            )

            data = json.loads(data_json.read_text(encoding="utf-8"))
            text = markdown.read_text(encoding="utf-8")
            prompt_files = list((root / "prompts").glob("*.md"))
            self.assertEqual(data["type"], "visual_prompt_pack")
            self.assertEqual(len(data["prompts"]), 3)
            self.assertIn("视觉爆款判断", text)
            self.assertEqual(len(prompt_files), 3)
            self.assertTrue(all("prompt_file" in item for item in data["prompts"]))

    def test_markdown_escapes_topic_quotes(self):
        diagnosis = {
            "type": "content_diagnosis",
            "topic": 'AI "工具" 定价',
            "source": "source.md",
            "core_insight": "工具定价取决于交付价值。",
            "cognitive_gap": "用户常把价格和成本混在一起。",
            "rewrite_angle": "从交付结果反推价格。",
            "visual_strategy": {
                "fit_score": 7,
                "explosive_potential": "定价争议有清晰反差。",
                "logic_check": "价格锚点和交付价值可以视觉化。",
                "audience_hook": "这个工具到底卖多少钱。",
                "style_keywords": ["商业"],
                "metaphors": ["价格标签"],
                "avoid": [],
                "asset_suggestions": [],
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            diagnosis_json = root / "diagnosis.json"
            diagnosis_json.write_text(json.dumps(diagnosis, ensure_ascii=False), encoding="utf-8")
            markdown = root / "visual.md"
            data_json = root / "visual.json"

            MODULE.write_prompt_pack(
                diagnosis_json=diagnosis_json,
                output_dir=root,
                stem="pricing",
                assets=["wechat-cover"],
                markdown_path=markdown,
                json_path=data_json,
            )

            text = markdown.read_text(encoding="utf-8")
            self.assertIn('topic: "AI \\"工具\\" 定价"', text)


if __name__ == "__main__":
    unittest.main()
