import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "make_content_diagnosis.py"
SPEC = importlib.util.spec_from_file_location("make_content_diagnosis", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def sample_payload(**overrides):
    payload = {
        "topic": "AI 内容工具",
        "source": 'source "quoted".md',
        "verdict": "值得改写，但需要换角度",
        "content_value": 8,
        "propagation_value": 7,
        "priority": "高",
        "core_insight": "工具价值来自降低内容生产摩擦",
        "cognitive_gap": "用户以为卖点是自动化，实际卖点是确定性交付",
        "rewrite_angle": "从功能介绍改为使用场景科普",
        "dimensions": [
            {"name": "标题|封面", "judgement": "可强化", "note": "原始标题缺少认知冲突|保存理由"},
            {"name": "表达效率", "judgement": "中等", "note": "需要压缩铺垫"},
        ],
        "keep_points": ["交付物清单", "后台生成逻辑"],
        "drop_points": ["过度技术细节"],
        "risk_notes": ["不要承诺平台自动发布"],
        "platform_strategies": [
            {"platform": "小红书", "fit": "高", "angle": "科普帖：普通人怎么判断工具值不值"},
            {"platform": "播客", "fit": "中高", "angle": "用对话解释工具价值与边界"},
        ],
        "podcast_strategy": {
            "angle": "围绕工具价值和适用人群展开",
            "listener_profile": "想提高内容生产效率的创作者",
            "opening_hook": "为什么自动化工具卖不动，交付确定性反而更值钱？",
            "tone": "克制、清晰、偏商业分析",
            "title": "AI内容工具到底值多少钱",
            "description": "从交付结果、使用门槛和平台边界三个角度，拆解这类工具为什么有价值，以及什么人不适合购买。",
            "cover_direction": "深色极简背景，主标题突出工具价值判断",
            "must_cover_points": ["价值不是自动化本身", "适合人群与不适合人群"],
            "skip_points": ["安装细节"],
        },
    }
    payload.update(overrides)
    return payload


class ContentDiagnosisTests(unittest.TestCase):
    def test_write_outputs_markdown_and_json_with_podcast_strategy(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            markdown = Path(temp_dir) / "diagnosis.md"
            data_json = Path(temp_dir) / "diagnosis.json"

            MODULE.write_diagnosis(markdown_path=markdown, json_path=data_json, **sample_payload())

            text = markdown.read_text(encoding="utf-8")
            data = json.loads(data_json.read_text(encoding="utf-8"))
            self.assertIn('type: "content_diagnosis"', text)
            self.assertIn("内容价值：8/10", text)
            self.assertIn("传播价值：7/10", text)
            self.assertIn("## 播客策略", text)
            self.assertEqual(data["type"], "content_diagnosis")
            self.assertEqual(data["podcast_strategy"]["title"], "AI内容工具到底值多少钱")

    def test_write_outputs_visual_strategy_when_present(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            markdown = Path(temp_dir) / "diagnosis.md"
            data_json = Path(temp_dir) / "diagnosis.json"

            MODULE.write_diagnosis(
                markdown_path=markdown,
                json_path=data_json,
                **sample_payload(
                    visual_strategy={
                        "fit_score": 8,
                        "explosive_potential": "认知反差明确，适合用封面先制造问题感。",
                        "logic_check": "从误区到反差再到判断框架，视觉逻辑成立。",
                        "audience_hook": "普通创作者最想知道这类工具到底值不值。",
                        "style_keywords": ["知识卡", "商业判断"],
                        "metaphors": ["放大镜", "交付流水线"],
                        "avoid": ["夸张收益承诺"],
                        "asset_suggestions": [
                            {
                                "asset": "wechat-cover",
                                "fit": "高",
                                "direction": "极简商业封面，突出价值判断",
                            }
                        ],
                    }
                ),
            )

            text = markdown.read_text(encoding="utf-8")
            data = json.loads(data_json.read_text(encoding="utf-8"))
            self.assertIn("## 视觉与爆款诊断", text)
            self.assertIn("视觉适配：8/10", text)
            self.assertEqual(data["visual_strategy"]["fit_score"], 8)
            self.assertEqual(data["visual_strategy"]["asset_suggestions"][0]["asset"], "wechat-cover")

    def test_markdown_escapes_frontmatter_quotes_and_table_pipes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            markdown = Path(temp_dir) / "diagnosis.md"
            data_json = Path(temp_dir) / "diagnosis.json"

            MODULE.write_diagnosis(
                markdown_path=markdown,
                json_path=data_json,
                **sample_payload(source='source "quoted"\nnext.md'),
            )

            text = markdown.read_text(encoding="utf-8")
            self.assertIn('source: "source \\"quoted\\" next.md"', text)
            self.assertIn("标题\\|封面", text)
            self.assertIn("认知冲突\\|保存理由", text)

    def test_rejects_empty_podcast_strategy_fields(self):
        payload = sample_payload(
            podcast_strategy={
                "angle": " ",
                "listener_profile": "创作者",
                "opening_hook": "为什么值得听？",
                "tone": "清晰",
                "title": "标题",
                "description": "简介",
                "cover_direction": "封面",
                "must_cover_points": ["重点"],
                "skip_points": [],
            }
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                MODULE.write_diagnosis(
                    markdown_path=Path(temp_dir) / "diagnosis.md",
                    json_path=Path(temp_dir) / "diagnosis.json",
                    **payload,
                )

    def test_bounded_score_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            MODULE.bounded_score("11", "content_value")

    def test_write_rejects_out_of_range_scores_when_called_directly(self):
        payload = sample_payload(content_value=12)

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                MODULE.write_diagnosis(
                    markdown_path=Path(temp_dir) / "diagnosis.md",
                    json_path=Path(temp_dir) / "diagnosis.json",
                    **payload,
                )


if __name__ == "__main__":
    unittest.main()
