import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "make_platform_quality_guardrail.py"
SPEC = importlib.util.spec_from_file_location("make_platform_quality_guardrail", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class PlatformQualityGuardrailTests(unittest.TestCase):
    def test_write_guardrail_outputs_markdown_and_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            markdown = Path(temp_dir) / "guardrail.md"
            data_json = Path(temp_dir) / "guardrail.json"

            MODULE.write_guardrail(
                markdown_path=markdown,
                json_path=data_json,
                topic="公众号低创作度避坑",
                source="source.md",
                verdict="可生成，但必须补原创判断和具体案例，避免像搬运总结。",
                risk_level="medium",
                low_creation_score=6,
                distribution_risk_score=7,
                checks=[
                    {
                        "name": "搬运洗稿",
                        "level": "high",
                        "evidence": "原文信息密度高，直接改写容易像复述。",
                        "fix": "重构为自己的判断框架，保留事实但换叙事。",
                    },
                    {
                        "name": "低价值AIGC",
                        "level": "medium",
                        "evidence": "若使用模板化排比会降低原创感。",
                        "fix": "加入具体场景、反例和平台经验。",
                    },
                ],
                must_do=["加入原创判断", "给出可验证案例"],
                must_avoid=["直接拼接原文段落", "标题过度承诺"],
                platform_rules=[
                    {"platform": "微信", "rule": "标题克制，正文有原创增量和风险提示。"},
                    {"platform": "小红书", "rule": "做成科普帖，不做伪干货或焦虑标题。"},
                ],
                rewrite_strategy="先提炼核心判断，再用新结构重写，最后做低创作度自检。",
                post_generation_checklist=["标题不夸大", "正文不复读", "无二维码私域诱导"],
            )

            text = markdown.read_text(encoding="utf-8")
            data = json.loads(data_json.read_text(encoding="utf-8"))
            self.assertIn('type: "platform_quality_guardrail"', text)
            self.assertIn("低创作度风险：6/10", text)
            self.assertIn("搬运洗稿", text)
            self.assertEqual(data["type"], "platform_quality_guardrail")
            self.assertEqual(data["checks"][0]["name"], "搬运洗稿")
            self.assertEqual(data["platform_rules"][1]["platform"], "小红书")

    def test_rejects_missing_checks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                MODULE.write_guardrail(
                    markdown_path=Path(temp_dir) / "guardrail.md",
                    json_path=Path(temp_dir) / "guardrail.json",
                    topic="空检查",
                    source="source.md",
                    verdict="缺少检查项",
                    risk_level="low",
                    low_creation_score=1,
                    distribution_risk_score=1,
                    checks=[],
                    must_do=["补判断"],
                    must_avoid=["搬运"],
                    platform_rules=[],
                    rewrite_strategy="重写",
                    post_generation_checklist=["自检"],
                )


if __name__ == "__main__":
    unittest.main()
