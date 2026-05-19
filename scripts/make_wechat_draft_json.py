"""Build a WeChat Official Account draft JSON from article metadata and HTML."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip().splitlines()
    meta: dict[str, str] = {}
    for line in raw:
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"')
    body = text[text.find("\n", end + 1) + 1 :]
    return meta, body


def normalize_source_url(value: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return value.strip()
    return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--markdown", required=True, help="Source Markdown with frontmatter")
    parser.add_argument("--html", required=True, help="WeChat-compatible HTML file")
    parser.add_argument("--thumb-media-id", required=True, help="Cover media_id from md2wechat upload_image")
    parser.add_argument("--output", required=True, help="Draft JSON output path")
    parser.add_argument("--title", help="Override title")
    parser.add_argument("--author", help="Override author")
    parser.add_argument("--digest", help="Override digest")
    parser.add_argument("--source-url", help="Override content_source_url")
    args = parser.parse_args()

    markdown_path = Path(args.markdown)
    meta, _ = parse_frontmatter(markdown_path.read_text(encoding="utf-8"))
    content = Path(args.html).read_text(encoding="utf-8")

    title = (args.title or meta.get("title") or markdown_path.stem)[:32]
    author = (args.author or meta.get("author") or "")[:16]
    digest = (args.digest or meta.get("digest") or meta.get("description") or title)[:128]
    source_url = normalize_source_url(args.source_url or meta.get("source") or "")

    article = {
        "title": title,
        "author": author,
        "digest": digest,
        "content": content,
        "content_source_url": source_url,
        "thumb_media_id": args.thumb_media_id,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"articles": [article]}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
