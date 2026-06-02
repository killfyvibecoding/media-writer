#!/usr/bin/env python3
"""Package a Xiaohongshu-ready explainer post as Markdown plus JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Iterable


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def normalize_tags(tags: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for raw in tags:
        tag = clean(raw).lstrip("#")
        if not tag:
            continue
        value = f"#{tag}"
        if value not in seen:
            normalized.append(value)
            seen.add(value)
    return normalized


def parse_sections(values: Iterable[str]) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    for raw in values:
        if "::" in raw:
            heading, body = raw.split("::", 1)
        else:
            heading, body = "正文", raw
        points = [clean(part) for part in re.split(r"\s*;\s*", body) if clean(part)]
        if points:
            sections.append((clean(heading), points))
    return sections


def render_markdown(
    *,
    titles: list[str],
    post_type: str,
    hook: str,
    body_sections: list[tuple[str, list[str]]],
    tags: list[str],
    cover_suggestion: str,
    source: str,
) -> str:
    lines: list[str] = [
        "---",
        f'title: "{titles[0]}"',
        'platform: "xiaohongshu"',
        f'post_type: "{post_type}"',
        f'source: "{source}"',
        "---",
        "",
        f"# 小红书{post_type}",
        "",
        f"帖子类型：{post_type}",
        "",
        "## 标题候选",
    ]
    lines.extend(f"{index}. {title}" for index, title in enumerate(titles, start=1))
    lines.extend(["", "## 正文", "", hook, ""])
    for heading, points in body_sections:
        lines.append(f"### {heading}")
        lines.extend(points)
        lines.append("")
    lines.extend(["## 热门相关标签", "", " ".join(tags), "", "## 封面建议", "", cover_suggestion, ""])
    return "\n".join(lines)


def write_post(
    *,
    markdown_path: Path,
    json_path: Path,
    titles: list[str],
    post_type: str = "科普帖",
    hook: str,
    body_sections: list[tuple[str, list[str]]],
    tags: list[str],
    cover_suggestion: str,
    source: str,
) -> None:
    titles = [clean(title) for title in titles if clean(title)]
    post_type = clean(post_type) or "科普帖"
    if not titles:
        raise ValueError("at least one title is required")
    hook = clean(hook)
    if not hook:
        raise ValueError("hook cannot be empty")
    tags = normalize_tags(tags)
    if len(tags) < 5:
        raise ValueError("provide at least 5 Xiaohongshu tags")
    if not body_sections:
        raise ValueError("at least one body section is required")

    payload = {
        "platform": "xiaohongshu",
        "post_type": post_type,
        "titles": titles,
        "hook": hook,
        "body_sections": [{"heading": h, "points": p} for h, p in body_sections],
        "tags": tags,
        "cover_suggestion": clean(cover_suggestion),
        "source": source,
    }
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(
        render_markdown(
            titles=titles,
            post_type=post_type,
            hook=hook,
            body_sections=body_sections,
            tags=tags,
            cover_suggestion=payload["cover_suggestion"],
            source=source,
        ),
        encoding="utf-8",
    )
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Xiaohongshu explainer post package.")
    parser.add_argument("--title", action="append", required=True, help="Title candidate. Repeat for multiple.")
    parser.add_argument("--post-type", default="科普帖", help="Xiaohongshu post type. Defaults to 科普帖.")
    parser.add_argument("--hook", required=True, help="Opening hook.")
    parser.add_argument(
        "--section",
        action="append",
        required=True,
        help='Section as "heading::point one; point two". Repeat for multiple.',
    )
    parser.add_argument("--tag", action="append", required=True, help="Related hashtag. Repeat at least 5 times.")
    parser.add_argument("--cover-suggestion", required=True, help="Cover copy/layout suggestion.")
    parser.add_argument("--source", default="", help="Original source path or URL.")
    parser.add_argument("--markdown", required=True, help="Output Markdown path.")
    parser.add_argument("--json", required=True, help="Output JSON path.")
    args = parser.parse_args()

    write_post(
        markdown_path=Path(args.markdown),
        json_path=Path(args.json),
        titles=args.title,
        post_type=args.post_type,
        hook=args.hook,
        body_sections=parse_sections(args.section),
        tags=args.tag,
        cover_suggestion=args.cover_suggestion,
        source=args.source,
    )
    print(args.markdown)
    print(args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
