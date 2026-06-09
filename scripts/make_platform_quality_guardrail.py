#!/usr/bin/env python3
"""Create a platform quality guardrail package as Markdown plus JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Iterable


VALID_LEVELS = {"low", "medium", "high", "critical"}


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def yaml_quote(value: object) -> str:
    text = clean(str(value))
    text = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def markdown_cell(value: object) -> str:
    return clean(str(value)).replace("|", "\\|")


def bounded_score(value: int | str, field: str) -> int:
    try:
        score = int(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an integer from 0 to 10") from exc
    if score < 0 or score > 10:
        raise ValueError(f"{field} must be from 0 to 10")
    return score


def normalize_level(value: str, field: str = "risk_level") -> str:
    level = clean(value).lower()
    if level not in VALID_LEVELS:
        raise ValueError(f"{field} must be one of: {', '.join(sorted(VALID_LEVELS))}")
    return level


def clean_list(values: Iterable[str]) -> list[str]:
    return [clean(value) for value in values if clean(value)]


def parse_check(values: Iterable[str]) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    for raw in values:
        parts = [clean(part) for part in raw.split("::", 3)]
        if len(parts) != 4:
            raise ValueError('check must be "name::level::evidence::fix"')
        name, level, evidence, fix = parts
        if not name or not evidence or not fix:
            raise ValueError("check fields cannot be empty")
        checks.append(
            {
                "name": name,
                "level": normalize_level(level, f"check {name} level"),
                "evidence": evidence,
                "fix": fix,
            }
        )
    return checks


def parse_platform_rule(values: Iterable[str]) -> list[dict[str, str]]:
    rules: list[dict[str, str]] = []
    for raw in values:
        parts = [clean(part) for part in raw.split("::", 1)]
        if len(parts) != 2:
            raise ValueError('platform rule must be "platform::rule"')
        platform, rule = parts
        if not platform or not rule:
            raise ValueError("platform rule fields cannot be empty")
        rules.append({"platform": platform, "rule": rule})
    return rules


def normalize_checks(values: list[dict[str, str]]) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    for item in values:
        normalized = {
            "name": clean(str(item.get("name", ""))),
            "level": normalize_level(str(item.get("level", "")), "check level"),
            "evidence": clean(str(item.get("evidence", ""))),
            "fix": clean(str(item.get("fix", ""))),
        }
        if not normalized["name"] or not normalized["evidence"] or not normalized["fix"]:
            raise ValueError("check fields cannot be empty")
        checks.append(normalized)
    if not checks:
        raise ValueError("at least one quality check is required")
    return checks


def normalize_platform_rules(values: list[dict[str, str]]) -> list[dict[str, str]]:
    rules: list[dict[str, str]] = []
    for item in values:
        normalized = {
            "platform": clean(str(item.get("platform", ""))),
            "rule": clean(str(item.get("rule", ""))),
        }
        if not normalized["platform"] or not normalized["rule"]:
            raise ValueError("platform rule fields cannot be empty")
        rules.append(normalized)
    return rules


def render_markdown(payload: dict[str, object]) -> str:
    checks = payload["checks"]
    platform_rules = payload["platform_rules"]
    assert isinstance(checks, list)
    assert isinstance(platform_rules, list)

    lines: list[str] = [
        "---",
        f"topic: {yaml_quote(payload['topic'])}",
        'type: "platform_quality_guardrail"',
        f"source: {yaml_quote(payload['source'])}",
        "---",
        "",
        f"# 平台质量闸门：{payload['topic']}",
        "",
        "## 总判断",
        "",
        f"- 结论：{payload['verdict']}",
        f"- 总体风险：{payload['risk_level']}",
        f"- 低创作度风险：{payload['low_creation_score']}/10",
        f"- 限流/分发风险：{payload['distribution_risk_score']}/10",
        f"- 改写策略：{payload['rewrite_strategy']}",
        "",
        "## 风险检查",
        "",
        "| 检查项 | 风险等级 | 证据 | 修正动作 |",
        "| --- | --- | --- | --- |",
    ]
    for item in checks:
        assert isinstance(item, dict)
        lines.append(
            "| "
            f"{markdown_cell(item['name'])} | "
            f"{markdown_cell(item['level'])} | "
            f"{markdown_cell(item['evidence'])} | "
            f"{markdown_cell(item['fix'])} |"
        )

    for title, key in [("必须做到", "must_do"), ("必须避免", "must_avoid")]:
        lines.extend(["", f"## {title}", ""])
        values = payload[key]
        assert isinstance(values, list)
        if values:
            lines.extend(f"- {value}" for value in values)
        else:
            lines.append("- 无")

    lines.extend(["", "## 分平台规则", "", "| 平台 | 规则 |", "| --- | --- |"])
    if platform_rules:
        for item in platform_rules:
            assert isinstance(item, dict)
            lines.append(f"| {markdown_cell(item['platform'])} | {markdown_cell(item['rule'])} |")
    else:
        lines.append("| 通用 | 先保证原创增量、风险降调和平台合规。 |")

    checklist = payload["post_generation_checklist"]
    assert isinstance(checklist, list)
    lines.extend(["", "## 生成后自检清单", ""])
    if checklist:
        lines.extend(f"- [ ] {item}" for item in checklist)
    else:
        lines.append("- [ ] 标题、正文、图片和 CTA 均通过低创作度/限流风险检查。")
    lines.append("")
    return "\n".join(lines)


def write_guardrail(
    *,
    markdown_path: Path,
    json_path: Path,
    topic: str,
    source: str,
    verdict: str,
    risk_level: str,
    low_creation_score: int,
    distribution_risk_score: int,
    checks: list[dict[str, str]],
    must_do: list[str],
    must_avoid: list[str],
    platform_rules: list[dict[str, str]],
    rewrite_strategy: str,
    post_generation_checklist: list[str],
) -> None:
    payload: dict[str, object] = {
        "type": "platform_quality_guardrail",
        "topic": clean(topic),
        "source": clean(source),
        "verdict": clean(verdict),
        "risk_level": normalize_level(risk_level),
        "low_creation_score": bounded_score(low_creation_score, "low_creation_score"),
        "distribution_risk_score": bounded_score(distribution_risk_score, "distribution_risk_score"),
        "checks": normalize_checks(checks),
        "must_do": clean_list(must_do),
        "must_avoid": clean_list(must_avoid),
        "platform_rules": normalize_platform_rules(platform_rules),
        "rewrite_strategy": clean(rewrite_strategy),
        "post_generation_checklist": clean_list(post_generation_checklist),
    }
    if not payload["topic"] or not payload["verdict"] or not payload["rewrite_strategy"]:
        raise ValueError("topic, verdict, and rewrite_strategy cannot be empty")

    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a platform quality guardrail package.")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--source", default="")
    parser.add_argument("--verdict", required=True)
    parser.add_argument("--risk-level", required=True, choices=sorted(VALID_LEVELS))
    parser.add_argument("--low-creation-score", required=True, type=int)
    parser.add_argument("--distribution-risk-score", required=True, type=int)
    parser.add_argument("--check", action="append", required=True, help='Repeat: "name::level::evidence::fix"')
    parser.add_argument("--must-do", action="append", default=[])
    parser.add_argument("--must-avoid", action="append", default=[])
    parser.add_argument("--platform-rule", action="append", default=[], help='Repeat: "platform::rule"')
    parser.add_argument("--rewrite-strategy", required=True)
    parser.add_argument("--post-check", action="append", default=[])
    parser.add_argument("--markdown", required=True)
    parser.add_argument("--json", required=True)
    args = parser.parse_args()

    write_guardrail(
        markdown_path=Path(args.markdown),
        json_path=Path(args.json),
        topic=args.topic,
        source=args.source,
        verdict=args.verdict,
        risk_level=args.risk_level,
        low_creation_score=args.low_creation_score,
        distribution_risk_score=args.distribution_risk_score,
        checks=parse_check(args.check),
        must_do=args.must_do,
        must_avoid=args.must_avoid,
        platform_rules=parse_platform_rule(args.platform_rule),
        rewrite_strategy=args.rewrite_strategy,
        post_generation_checklist=args.post_check,
    )
    print(args.markdown)
    print(args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
