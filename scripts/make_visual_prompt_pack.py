#!/usr/bin/env python3
"""Create a diagnosis-driven visual prompt pack for media-writer outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Iterable


ASSET_DEFAULTS = {
    "wechat-cover": {
        "label": "微信公众号封面",
        "aspect": "16:9",
        "text": "title-subtitle",
        "mood": "balanced",
        "font": "clean",
    },
    "podcast-cover": {
        "label": "播客封面",
        "aspect": "16:9",
        "text": "title-subtitle",
        "mood": "balanced",
        "font": "clean",
    },
    "xiaohongshu-cover": {
        "label": "小红书首图",
        "aspect": "3:4",
        "text": "text-rich",
        "mood": "bold",
        "font": "display",
    },
    "ppt-cover": {
        "label": "PPT封面",
        "aspect": "16:9",
        "text": "title-only",
        "mood": "subtle",
        "font": "clean",
    },
    "article-illustration": {
        "label": "文章配图",
        "aspect": "16:9",
        "text": "none",
        "mood": "balanced",
        "font": "clean",
    },
    "infographic": {
        "label": "信息图",
        "aspect": "3:4",
        "text": "text-rich",
        "mood": "balanced",
        "font": "clean",
    },
}


STYLE_PRESETS = {
    "business": ("metaphor", "elegant", "screen-print", "editorial", "serif"),
    "technical": ("conceptual", "cool", "digital", "blueprint", "clean"),
    "ai": ("conceptual", "cool", "digital", "blueprint", "clean"),
    "education": ("conceptual", "macaron", "hand-drawn", "hand-drawn-edu", "clean"),
    "story": ("scene", "warm", "hand-drawn", "warm", "handwritten"),
    "emotion": ("scene", "warm", "painterly", "watercolor", "handwritten"),
    "warning": ("typography", "dark", "screen-print", "poster-art", "display"),
    "retro": ("scene", "retro", "digital", "retro", "serif"),
    "minimal": ("minimal", "mono", "flat-vector", "minimal", "clean"),
}


LAYOUT_BY_ASSET = {
    "wechat-cover": "hero",
    "podcast-cover": "hero",
    "xiaohongshu-cover": "sparse-hook-card",
    "ppt-cover": "premium-title-slide",
    "article-illustration": "concept-scene",
    "infographic": "bento-grid",
}


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value).strip())


def yaml_quote(value: object) -> str:
    text = clean(value)
    text = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def clean_list(values: Iterable[object]) -> list[str]:
    return [clean(value) for value in values if clean(value)]


def asset_filename(asset: str, index: int) -> str:
    safe = re.sub(r"[^a-z0-9-]+", "-", asset.lower()).strip("-")
    return f"{index:02d}-{safe}.md"


def load_diagnosis(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("diagnosis JSON must be an object")
    if data.get("type") != "content_diagnosis":
        raise ValueError("diagnosis JSON must have type=content_diagnosis")
    return data


def pick_style_signal(text: str, style_keywords: list[str]) -> str:
    haystack = f"{text} {' '.join(style_keywords)}".lower()
    rules = [
        ("warning", ["警惕", "风险", "避坑", "危机", "warning", "critical", "must"]),
        ("technical", ["技术", "架构", "系统", "芯片", "算力", "数据中心", "api", "model"]),
        ("ai", ["ai", "人工智能", "gpu", "cuda", "agent", "大模型"]),
        ("education", ["科普", "教程", "概念", "学习", "知识", "方法", "framework"]),
        ("story", ["故事", "人物", "经历", "创业", "叙事", "journey", "narrative"]),
        ("emotion", ["情绪", "焦虑", "孤独", "共鸣", "生活", "human"]),
        ("retro", ["历史", "复古", "经典", "昨天", "回忆", "vintage"]),
        ("minimal", ["极简", "本质", "核心", "简单", "zen", "focus"]),
        ("business", ["商业", "管理", "战略", "公司", "投资", "市场", "business"]),
    ]
    for signal, keywords in rules:
        if any(keyword in haystack for keyword in keywords):
            return signal
    return "business"


def infer_dimensions(diagnosis: dict[str, object], asset: str) -> dict[str, str]:
    visual = diagnosis.get("visual_strategy")
    visual = visual if isinstance(visual, dict) else {}
    style_keywords = clean_list(visual.get("style_keywords", [])) if visual else []
    text = " ".join(
        clean(diagnosis.get(field, ""))
        for field in ["topic", "core_insight", "cognitive_gap", "rewrite_angle"]
    )
    signal = pick_style_signal(text, style_keywords)
    image_type, palette, rendering, preset, font = STYLE_PRESETS[signal]
    defaults = ASSET_DEFAULTS[asset]

    if asset == "infographic":
        image_type = "infographic"
        preset = "knowledge-card" if signal in {"technical", "ai", "education"} else "pro-summary"
    elif asset == "article-illustration":
        image_type = "scene" if signal in {"story", "emotion", "retro"} else "conceptual"
        defaults = {**defaults, "text": "none"}
    elif asset == "xiaohongshu-cover":
        preset = "knowledge-card" if signal in {"technical", "ai", "education"} else "poster"
        defaults = {**defaults, "mood": "bold"}

    return {
        "signal": signal,
        "type": image_type,
        "palette": palette,
        "rendering": rendering,
        "preset": preset,
        "layout": LAYOUT_BY_ASSET[asset],
        "aspect": clean(defaults["aspect"]),
        "text": clean(defaults["text"]),
        "mood": clean(defaults["mood"]),
        "font": font if font else clean(defaults["font"]),
    }


def prompt_body(
    *,
    diagnosis: dict[str, object],
    asset: str,
    dimensions: dict[str, str],
    prompt_title: str,
) -> str:
    visual = diagnosis.get("visual_strategy")
    visual = visual if isinstance(visual, dict) else {}
    metaphors = clean_list(visual.get("metaphors", [])) if visual else []
    avoid = clean_list(visual.get("avoid", [])) if visual else []
    hook = clean(visual.get("audience_hook", "")) if visual else ""
    logic = clean(visual.get("logic_check", "")) if visual else ""
    explosive = clean(visual.get("explosive_potential", "")) if visual else ""

    label = ASSET_DEFAULTS[asset]["label"]
    title = clean(diagnosis.get("topic", prompt_title))
    core = clean(diagnosis.get("core_insight", ""))
    gap = clean(diagnosis.get("cognitive_gap", ""))
    angle = clean(diagnosis.get("rewrite_angle", ""))

    visual_metaphors = "、".join(metaphors) if metaphors else "choose one precise visual metaphor from the core insight"
    avoid_line = "、".join(avoid) if avoid else "stock-photo cliches, fake UI, unreadable text, watermark, logo clutter"

    return f"""Create a publication-ready raster image for: {label}

Topic: {title}
Core insight: {core}
Cognitive gap: {gap}
Rewrite angle: {angle}
Audience hook: {hook}
Viral visual logic: {logic}
Explosive potential: {explosive}

Visual decision:
- Type: {dimensions['type']}
- Layout: {dimensions['layout']}
- Palette: {dimensions['palette']}
- Rendering: {dimensions['rendering']}
- Preset reference: {dimensions['preset']}
- Text level: {dimensions['text']}
- Mood: {dimensions['mood']}
- Font direction: {dimensions['font']}
- Aspect ratio: {dimensions['aspect']}

Composition requirements:
- Build the image around the current topic, not a reusable generic template.
- Use this visual metaphor direction: {visual_metaphors}.
- Make the first-view hook immediately legible for the target platform.
- Keep visual hierarchy clean: one main anchor, one supporting contrast, one subtle detail layer.
- If text is included, use short Chinese copy only; never render dense paragraphs.
- Leave safe margins for platform cropping.

Avoid:
- {avoid_line}
- Do not use stock market K-lines unless the source explicitly requires finance-market visuals.
- Do not use decorative gradients, generic AI robots, or unrelated futuristic city backgrounds.
- Do not imitate a real person's face unless a user-provided reference and permission are available.
"""


def write_prompt_file(path: Path, *, asset: str, dimensions: dict[str, str], body: str) -> None:
    frontmatter = [
        "---",
        f'asset: "{asset}"',
        f'aspect: "{dimensions["aspect"]}"',
        f'type: "{dimensions["type"]}"',
        f'palette: "{dimensions["palette"]}"',
        f'rendering: "{dimensions["rendering"]}"',
        f'preset: "{dimensions["preset"]}"',
        "---",
        "",
    ]
    path.write_text("\n".join(frontmatter) + body, encoding="utf-8")


def render_markdown(payload: dict[str, object]) -> str:
    visual = payload["visual_logic"]
    assert isinstance(visual, dict)
    lines = [
        "---",
        f"topic: {yaml_quote(payload['topic'])}",
        'type: "visual_prompt_pack"',
        "---",
        "",
        f"# 视觉提示词包：{payload['topic']}",
        "",
        "## 视觉爆款判断",
        "",
        f"- 视觉适配：{visual['fit_score']}/10",
        f"- 爆款潜力：{visual['explosive_potential']}",
        f"- 逻辑校验：{visual['logic_check']}",
        f"- 观众钩子：{visual['audience_hook']}",
        "",
        "## 提示词资产",
        "",
        "| 资产 | 尺寸 | 预设 | 类型 | 配色 | 渲染 | 提示词文件 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    prompts = payload["prompts"]
    assert isinstance(prompts, list)
    for item in prompts:
        assert isinstance(item, dict)
        dimensions = item["dimensions"]
        assert isinstance(dimensions, dict)
        lines.append(
            f"| {item['asset']} | {dimensions['aspect']} | {dimensions['preset']} | {dimensions['type']} | {dimensions['palette']} | {dimensions['rendering']} | {item['prompt_file']} |"
        )
    return "\n".join(lines) + "\n"


def write_prompt_pack(
    *,
    diagnosis_json: Path,
    output_dir: Path,
    stem: str,
    assets: list[str],
    markdown_path: Path,
    json_path: Path,
) -> None:
    diagnosis = load_diagnosis(diagnosis_json)
    selected_assets = assets or ["wechat-cover", "podcast-cover", "xiaohongshu-cover"]
    unsupported = [asset for asset in selected_assets if asset not in ASSET_DEFAULTS]
    if unsupported:
        raise ValueError(f"unsupported assets: {', '.join(unsupported)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    prompts_dir = output_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    visual = diagnosis.get("visual_strategy")
    visual = visual if isinstance(visual, dict) else {}
    visual_logic = {
        "fit_score": int(visual.get("fit_score", 0) or 0),
        "explosive_potential": clean(visual.get("explosive_potential", "未单独诊断，按内容价值和认知落差生成。")),
        "logic_check": clean(visual.get("logic_check", "以核心洞察、认知落差和平台策略校验视觉逻辑。")),
        "audience_hook": clean(visual.get("audience_hook", diagnosis.get("cognitive_gap", ""))),
    }

    prompt_items: list[dict[str, object]] = []
    for index, asset in enumerate(selected_assets, start=1):
        dimensions = infer_dimensions(diagnosis, asset)
        prompt_path = prompts_dir / asset_filename(asset, index)
        body = prompt_body(
            diagnosis=diagnosis,
            asset=asset,
            dimensions=dimensions,
            prompt_title=stem,
        )
        write_prompt_file(prompt_path, asset=asset, dimensions=dimensions, body=body)
        prompt_items.append(
            {
                "asset": asset,
                "label": ASSET_DEFAULTS[asset]["label"],
                "dimensions": dimensions,
                "prompt_file": str(prompt_path),
                "output_hint": str(output_dir / f"{stem}_{asset.replace('-', '_')}.png"),
                "prompt": body,
            }
        )

    payload: dict[str, object] = {
        "type": "visual_prompt_pack",
        "topic": clean(diagnosis.get("topic", stem)),
        "diagnosis_json": str(diagnosis_json),
        "visual_logic": visual_logic,
        "prompts": prompt_items,
    }
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a diagnosis-driven visual prompt pack.")
    parser.add_argument("--diagnosis-json", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--stem", required=True)
    parser.add_argument("--asset", action="append", default=[])
    parser.add_argument("--markdown", required=True)
    parser.add_argument("--json", required=True)
    args = parser.parse_args()

    write_prompt_pack(
        diagnosis_json=Path(args.diagnosis_json),
        output_dir=Path(args.output_dir),
        stem=args.stem,
        assets=args.asset,
        markdown_path=Path(args.markdown),
        json_path=Path(args.json),
    )
    print(args.markdown)
    print(args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
