"""Convert Markdown to WeChat-compatible HTML and upload local/remote images.

Usage:
    python publish_markdown_to_wechat.py <markdown_file> <md2wechat_exe>

Set MD2WECHAT_OUTPUT_DIR to choose where generated artifacts are written.
Set MD2WECHAT_SKIP_IMAGE_UPLOAD=1 to leave image URLs unchanged.
"""

from __future__ import annotations

import html
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path


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


def download(url: str, path: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "Codex"})
    path.write_bytes(urllib.request.urlopen(req, timeout=90).read())


def upload_image(tool: str, path: Path) -> str:
    raw = subprocess.check_output(
        [tool, "upload_image", str(path), "--json"],
        text=True,
        encoding="utf-8",
    )
    payload = json.loads(raw)
    if not payload.get("success"):
        raise RuntimeError(f"image upload failed for {path}: {payload}")
    return payload["data"]["wechat_url"]


def normalize_obsidian_images(body: str) -> str:
    def replace_with_alias(match: re.Match[str]) -> str:
        target = match.group(1).strip()
        alias = match.group(2).strip() or "图像"
        return f"![{alias}]({target})"

    body = re.sub(r"!\[\[([^\]|]+)\|([^\]]*)\]\]", replace_with_alias, body)
    body = re.sub(r"!\[\[([^\]]+)\]\]", lambda m: f"![图像]({m.group(1).strip()})", body)
    return body


def resolve_image_path(md_path: Path, src: str) -> Path:
    candidates = [
        md_path.parent / src,
        md_path.parent / "attachments" / src,
        md_path.parent.parent / src,
        md_path.parent.parent / "attachments" / src,
        Path(src),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return (md_path.parent / src).resolve()


def inline_html(text: str) -> str:
    escaped = html.escape(text.strip())
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^\)]+)\)",
        r'<a href="\2" style="color:#2563eb;text-decoration:none;border-bottom:1px solid #bfdbfe;">\1</a>',
        escaped,
    )
    escaped = re.sub(
        r"\*\*([^*]+)\*\*",
        r'<strong style="color:#111827;font-weight:800;">\1</strong>',
        escaped,
    )
    escaped = re.sub(
        r"`([^`]+)`",
        r'<code style="background:#f1f5f9;border-radius:4px;padding:2px 5px;font-family:Consolas,monospace;font-size:0.92em;">\1</code>',
        escaped,
    )
    return escaped.replace("\n", "<br />")


def convert_body(body: str, image_urls: list[str]) -> str:
    lines = body.splitlines()
    out: list[str] = []
    para: list[str] = []
    code: list[str] = []
    in_code = False
    image_index = 0

    def flush_para() -> None:
        if para:
            out.append(f'<p style="margin:14px 0;color:#202124;">{inline_html(" ".join(para))}</p>')
            para.clear()

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                encoded = html.escape("\n".join(code))
                out.append(
                    '<pre style="white-space:pre-wrap;background:#f6f8fa;border:1px solid #d0d7de;'
                    f'border-radius:8px;padding:12px 14px;overflow:auto;font-size:13px;line-height:1.65;color:#24292f;">{encoded}</pre>'
                )
                code.clear()
                in_code = False
            else:
                flush_para()
                in_code = True
            continue
        if in_code:
            code.append(line)
            continue
        if not stripped:
            flush_para()
            continue
        if re.match(r"^!\[[^\]]*\]\([^)]+\)$", stripped):
            flush_para()
            if image_index < len(image_urls):
                url = html.escape(image_urls[image_index])
                out.append(
                    '<p style="margin:22px 0;text-align:center;">'
                    f'<img src="{url}" alt="图像" style="max-width:100%;height:auto;border-radius:8px;display:block;margin:0 auto;" />'
                    "</p>"
                )
                image_index += 1
            continue
        if stripped.startswith("# "):
            flush_para()
            out.append(
                '<h1 style="font-size:24px;line-height:1.35;margin:28px 0 16px;color:#111827;'
                f'font-weight:800;border-left:5px solid #2563eb;padding-left:12px;">{inline_html(stripped[2:])}</h1>'
            )
            continue
        if stripped.startswith("## "):
            flush_para()
            out.append(
                '<h2 style="font-size:21px;line-height:1.45;margin:24px 0 12px;color:#1f2937;'
                f'font-weight:800;">{inline_html(stripped[3:])}</h2>'
            )
            continue
        if stripped.startswith(">"):
            flush_para()
            out.append(
                '<blockquote style="margin:18px 0;padding:12px 14px;border-left:4px solid #94a3b8;'
                f'background:#f8fafc;color:#475569;border-radius:6px;">{inline_html(stripped.lstrip("> "))}</blockquote>'
            )
            continue
        if re.match(r"^[-*]\s+", stripped):
            flush_para()
            item = re.sub(r"^[-*]\s+", "", stripped)
            out.append(
                '<p style="margin:10px 0 10px 16px;color:#202124;">'
                f'<span style="color:#2563eb;font-weight:700;">•</span> {inline_html(item)}</p>'
            )
            continue
        para.append(stripped)
    flush_para()
    return "\n".join(out)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: publish_markdown_to_wechat.py <markdown_file> <md2wechat_exe>", file=sys.stderr)
        return 2

    md_path = Path(sys.argv[1])
    tool = sys.argv[2]
    text = md_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    body = normalize_obsidian_images(body)

    title = meta.get("title") or md_path.stem[:32]
    source = meta.get("source", "")
    author = meta.get("author", "")
    digest = meta.get("digest") or meta.get("description", "")[:120] or title

    stem = md_path.with_suffix("").name
    out_dir = Path(os.environ.get("MD2WECHAT_OUTPUT_DIR") or md_path.parent)
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_stem = re.sub(r'[<>:"/\\|?*]+', "_", stem)
    html_path = out_dir / f"{safe_stem}.wechat.html"
    map_path = out_dir / f"{safe_stem}.image-map.json"
    cover_path = out_dir / f"{safe_stem}_cover.jpg"

    skip_image_upload = os.environ.get("MD2WECHAT_SKIP_IMAGE_UPLOAD") == "1"
    image_matches = list(re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", body))
    image_urls: list[str] = []
    image_map: list[dict[str, str]] = []
    for i, match in enumerate(image_matches):
        src = match.group(1).strip("<>")
        parsed = urllib.parse.urlparse(src)
        suffix = Path(parsed.path).suffix or ".jpg"
        local = out_dir / f"{safe_stem}_image_{i}{suffix}"
        if skip_image_upload:
            image_urls.append(src)
            image_map.append({"index": str(i), "source": src, "local": "", "wechat_url": src})
            continue
        if parsed.scheme in {"http", "https"}:
            download(src, local)
        else:
            local = resolve_image_path(md_path, src)
        wechat_url = upload_image(tool, local)
        image_urls.append(wechat_url)
        image_map.append({"index": str(i), "source": src, "local": str(local), "wechat_url": wechat_url})
        if i == 0:
            cover_path.write_bytes(local.read_bytes())

    body_html = convert_body(body, image_urls)
    source_html = (
        f'<blockquote style="margin:22px 0 0;padding:12px 14px;border-left:4px solid #94a3b8;background:#f8fafc;color:#475569;border-radius:6px;">'
        f'来源：<span>{html.escape(source)}</span></blockquote>'
        if source
        else ""
    )
    final_html = f"""<section style="max-width:677px;margin:0 auto;padding:18px 12px;background:#ffffff;color:#202124;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;line-height:1.82;font-size:16px;letter-spacing:0;">
<h1 style="font-size:24px;line-height:1.35;margin:6px 0 12px;color:#111827;font-weight:800;">{html.escape(title)}</h1>
{body_html}
{source_html}
</section>
"""
    html_path.write_text(final_html, encoding="utf-8")
    map_path.write_text(json.dumps(image_map, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "title": title,
        "author": author,
        "digest": digest,
        "html": str(html_path),
        "cover": str(cover_path),
        "image_map": str(map_path),
        "images": len(image_map),
        "length": len(body),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
