#!/usr/bin/env python3
"""Package a pre-generation content diagnosis as Markdown plus JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Iterable


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def yaml_quote(value: object) -> str:
    text = clean(str(value))
    text = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def markdown_cell(value: object) -> str:
    return clean(str(value)).replace("|", "\\|")


def bounded_score(value: str, field: str) -> int:
    try:
        score = int(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an integer from 0 to 10") from exc
    if score < 0 or score > 10:
        raise ValueError(f"{field} must be from 0 to 10")
    return score


def parse_dimension(values: Iterable[str]) -> list[dict[str, str]]:
    dimensions: list[dict[str, str]] = []
    for raw in values:
        parts = [clean(part) for part in raw.split("::", 2)]
        if len(parts) != 3:
            raise ValueError('dimension must be "name::judgement::note"')
        name, judgement, note = parts
        if not name or not judgement or not note:
            raise ValueError("dimension fields cannot be empty")
        dimensions.append({"name": name, "judgement": judgement, "note": note})
    return dimensions


def parse_platform(values: Iterable[str]) -> list[dict[str, str]]:
    strategies: list[dict[str, str]] = []
    for raw in values:
        parts = [clean(part) for part in raw.split("::", 2)]
        if len(parts) != 3:
            raise ValueError('platform strategy must be "platform::fit::angle"')
        platform, fit, angle = parts
        if not platform or not fit or not angle:
            raise ValueError("platform strategy fields cannot be empty")
        strategies.append({"platform": platform, "fit": fit, "angle": angle})
    return strategies


def clean_list(values: Iterable[str]) -> list[str]:
    return [clean(value) for value in values if clean(value)]


def normalize_dimensions(values: list[dict[str, str]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in values:
        normalized_item = {
            "name": clean(str(item.get("name", ""))),
            "judgement": clean(str(item.get("judgement", ""))),
            "note": clean(str(item.get("note", ""))),
        }
        if not all(normalized_item.values()):
            raise ValueError("diagnostic dimension fields cannot be empty")
        normalized.append(normalized_item)
    return normalized


def normalize_platform_strategies(values: list[dict[str, str]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in values:
        normalized_item = {
            "platform": clean(str(item.get("platform", ""))),
            "fit": clean(str(item.get("fit", ""))),
            "angle": clean(str(item.get("angle", ""))),
        }
        if not all(normalized_item.values()):
            raise ValueError("platform strategy fields cannot be empty")
        normalized.append(normalized_item)
    return normalized


def normalize_podcast_strategy(strategy: dict[str, object]) -> dict[str, object]:
    required_fields = [
        "angle",
        "listener_profile",
        "opening_hook",
        "tone",
        "title",
        "description",
        "cover_direction",
    ]
    normalized: dict[str, object] = {}
    for field in required_fields:
        value = clean(str(strategy.get(field, "")))
        if not value:
            raise ValueError(f"podcast strategy field {field} cannot be empty")
        normalized[field] = value

    must_cover = strategy.get("must_cover_points", [])
    skip = strategy.get("skip_points", [])
    if not isinstance(must_cover, list) or not isinstance(skip, list):
        raise ValueError("podcast strategy points must be lists")
    normalized["must_cover_points"] = clean_list(str(point) for point in must_cover)
    normalized["skip_points"] = clean_list(str(point) for point in skip)
    if not normalized["must_cover_points"]:
        raise ValueError("podcast strategy must include must_cover_points")
    return normalized


def render_markdown(payload: dict[str, object]) -> str:
    dimensions = payload["dimensions"]
    platforms = payload["platform_strategies"]
    podcast = payload["podcast_strategy"]
    assert isinstance(dimensions, list)
    assert isinstance(platforms, list)
    assert isinstance(podcast, dict)

    lines: list[str] = [
        "---",
        f"topic: {yaml_quote(payload['topic'])}",
        'type: "content_diagnosis"',
        f"source: {yaml_quote(payload['source'])}",
        "---",
        "",
        f"# 内容诊断：{payload['topic']}",
        "",
        "## 总判断",
        "",
        f"- 结论：{payload['verdict']}",
        f"- 内容价值：{payload['content_value']}/10",
        f"- 传播价值：{payload['propagation_value']}/10",
        f"- 执行优先级：{payload['priority']}",
        f"- 核心洞察：{payload['core_insight']}",
        f"- 认知落差：{payload['cognitive_gap']}",
        f"- 推荐改写角度：{payload['rewrite_angle']}",
        "",
        "## 五维诊断",
        "",
        "| 维度 | 判断 | 说明 |",
        "| --- | --- | --- |",
    ]
    for item in dimensions:
        assert isinstance(item, dict)
        lines.append(
            f"| {markdown_cell(item['name'])} | {markdown_cell(item['judgement'])} | {markdown_cell(item['note'])} |"
        )

    lines.extend(["", "## 保留 / 弱化 / 风险", ""])
    for label, key in [("必须保留", "keep_points"), ("应该弱化", "drop_points"), ("风险提示", "risk_notes")]:
        lines.append(f"### {label}")
        values = payload[key]
        assert isinstance(values, list)
        if values:
            lines.extend(f"- {value}" for value in values)
        else:
            lines.append("- 无")
        lines.append("")

    lines.extend(["## 分平台策略", "", "| 平台 | 适配度 | 生成角度 |", "| --- | --- | --- |"])
    for item in platforms:
        assert isinstance(item, dict)
        lines.append(
            f"| {markdown_cell(item['platform'])} | {markdown_cell(item['fit'])} | {markdown_cell(item['angle'])} |"
        )

    lines.extend(
        [
            "",
            "## 播客策略",
            "",
            f"- 主角度：{podcast['angle']}",
            f"- 目标听众：{podcast['listener_profile']}",
            f"- 开场钩子：{podcast['opening_hook']}",
            f"- 语气：{podcast['tone']}",
            f"- 标题：{podcast['title']}",
            f"- 简介：{podcast['description']}",
            f"- 封面方向：{podcast['cover_direction']}",
            "",
            "### 必讲点",
        ]
    )
    for point in podcast["must_cover_points"]:
        lines.append(f"- {point}")
    lines.extend(["", "### 弱化点"])
    skip_points = podcast["skip_points"]
    assert isinstance(skip_points, list)
    if skip_points:
        for point in skip_points:
            lines.append(f"- {point}")
    else:
        lines.append("- 无")
    return "\n".join(lines) + "\n"


def write_diagnosis(
    *,
    markdown_path: Path,
    json_path: Path,
    topic: str,
    source: str,
    verdict: str,
    content_value: int,
    propagation_value: int,
    priority: str,
    core_insight: str,
    cognitive_gap: str,
    rewrite_angle: str,
    dimensions: list[dict[str, str]],
    keep_points: list[str],
    drop_points: list[str],
    risk_notes: list[str],
    platform_strategies: list[dict[str, str]],
    podcast_strategy: dict[str, object],
) -> None:
    content_value = bounded_score(str(content_value), "content_value")
    propagation_value = bounded_score(str(propagation_value), "propagation_value")
    dimensions = normalize_dimensions(dimensions)
    platform_strategies = normalize_platform_strategies(platform_strategies)
    podcast_strategy = normalize_podcast_strategy(podcast_strategy)
    if not dimensions:
        raise ValueError("at least one diagnostic dimension is required")
    if not platform_strategies:
        raise ValueError("at least one platform strategy is required")

    payload: dict[str, object] = {
        "type": "content_diagnosis",
        "topic": clean(topic),
        "source": clean(source),
        "verdict": clean(verdict),
        "content_value": content_value,
        "propagation_value": propagation_value,
        "priority": clean(priority),
        "core_insight": clean(core_insight),
        "cognitive_gap": clean(cognitive_gap),
        "rewrite_angle": clean(rewrite_angle),
        "dimensions": dimensions,
        "keep_points": clean_list(keep_points),
        "drop_points": clean_list(drop_points),
        "risk_notes": clean_list(risk_notes),
        "platform_strategies": platform_strategies,
        "podcast_strategy": podcast_strategy,
    }
    for field in ["topic", "verdict", "priority", "core_insight", "cognitive_gap", "rewrite_angle"]:
        if not payload[field]:
            raise ValueError(f"{field} cannot be empty")

    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a media-writer content diagnosis package.")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--source", default="")
    parser.add_argument("--verdict", required=True)
    parser.add_argument("--content-value", required=True)
    parser.add_argument("--propagation-value", required=True)
    parser.add_argument("--priority", required=True)
    parser.add_argument("--core-insight", required=True)
    parser.add_argument("--cognitive-gap", required=True)
    parser.add_argument("--rewrite-angle", required=True)
    parser.add_argument("--dimension", action="append", required=True, help='Repeat: "name::judgement::note"')
    parser.add_argument("--keep", action="append", default=[])
    parser.add_argument("--drop", action="append", default=[])
    parser.add_argument("--risk", action="append", default=[])
    parser.add_argument("--platform", action="append", required=True, help='Repeat: "platform::fit::angle"')
    parser.add_argument("--podcast-angle", required=True)
    parser.add_argument("--podcast-listener", required=True)
    parser.add_argument("--podcast-hook", required=True)
    parser.add_argument("--podcast-tone", required=True)
    parser.add_argument("--podcast-title", required=True)
    parser.add_argument("--podcast-description", required=True)
    parser.add_argument("--podcast-cover-direction", required=True)
    parser.add_argument("--podcast-point", action="append", required=True)
    parser.add_argument("--podcast-skip", action="append", default=[])
    parser.add_argument("--markdown", required=True)
    parser.add_argument("--json", required=True)
    args = parser.parse_args()

    write_diagnosis(
        markdown_path=Path(args.markdown),
        json_path=Path(args.json),
        topic=args.topic,
        source=args.source,
        verdict=args.verdict,
        content_value=bounded_score(args.content_value, "content_value"),
        propagation_value=bounded_score(args.propagation_value, "propagation_value"),
        priority=args.priority,
        core_insight=args.core_insight,
        cognitive_gap=args.cognitive_gap,
        rewrite_angle=args.rewrite_angle,
        dimensions=parse_dimension(args.dimension),
        keep_points=clean_list(args.keep),
        drop_points=clean_list(args.drop),
        risk_notes=clean_list(args.risk),
        platform_strategies=parse_platform(args.platform),
        podcast_strategy={
            "angle": clean(args.podcast_angle),
            "listener_profile": clean(args.podcast_listener),
            "opening_hook": clean(args.podcast_hook),
            "tone": clean(args.podcast_tone),
            "title": clean(args.podcast_title),
            "description": clean(args.podcast_description),
            "cover_direction": clean(args.podcast_cover_direction),
            "must_cover_points": clean_list(args.podcast_point),
            "skip_points": clean_list(args.podcast_skip),
        },
    )
    print(args.markdown)
    print(args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
