import importlib.util
from pathlib import Path
import sys
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_notebooklm_artifact.py"
SPEC = importlib.util.spec_from_file_location("run_notebooklm_artifact", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class NotebookLMArtifactTests(unittest.TestCase):
    def test_slides_prompt_uses_premium_design_module(self):
        prompt = MODULE.CHAT_PROMPTS["slides"]

        self.assertIn("专业的 PPT 设计师", prompt)
        self.assertIn("理解与决策结果", prompt)
        self.assertIn("中文版提示词", prompt)
        self.assertIn("English Prompt", prompt)
        self.assertIn("2026-05-25", prompt)
        self.assertIn("Apple / Linear / Notion", prompt)
        self.assertIn("16:9", prompt)
        self.assertNotIn("3-5 个要点", prompt)

    def test_slides_prompt_forbids_old_visual_style_failures(self):
        prompt = MODULE.CHAT_PROMPTS["slides"]

        for forbidden in ["粉色", "紫色", "彩虹渐变", "暖橙", "渐变文字", "发光效果"]:
            self.assertIn(forbidden, prompt)
        self.assertIn("全页不超过 3 种颜色", prompt)
        self.assertIn("留白占页面 40%-60%", prompt)


if __name__ == "__main__":
    unittest.main()
