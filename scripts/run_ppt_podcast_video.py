#!/usr/bin/env python3
"""Build a HyperFrames PPT+podcast dynamic video project and render MP4."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Callable, Iterable


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
AUDIO_EXTS = {".m4a", ".mp3", ".wav", ".aac", ".flac", ".ogg"}
DEFAULT_DURATION_PER_SLIDE = 8.0


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class HyperFramesCommandError(RuntimeError):
    def __init__(self, message: str, logs: list[dict[str, object]]):
        super().__init__(message)
        self.logs = logs


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def numeric_key(path: Path) -> tuple[int, str]:
    numbers = re.findall(r"\d+", path.stem)
    number = int(numbers[-1]) if numbers else 10**9
    return number, path.name.lower()


def sorted_slide_images(slide_dir: Path) -> list[Path]:
    if not slide_dir.exists():
        raise FileNotFoundError(f"slides source does not exist: {slide_dir}")
    if slide_dir.is_file():
        if slide_dir.suffix.lower() in IMAGE_EXTS:
            return [slide_dir.resolve()]
        raise ValueError(f"single slide source must be an image: {slide_dir}")
    images = [p.resolve() for p in slide_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    if not images:
        raise ValueError(f"no slide images found in {slide_dir}")
    return sorted(images, key=numeric_key)


def export_pdf_to_images(pdf_path: Path, image_dir: Path) -> list[Path]:
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise RuntimeError("pdftoppm is required to export PDF slides to images")
    image_dir.mkdir(parents=True, exist_ok=True)
    prefix = image_dir / "page"
    result = subprocess.run(
        [pdftoppm, "-png", "-r", "150", str(pdf_path), str(prefix)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pdftoppm failed for {pdf_path}: {result.stderr or result.stdout}")
    return sorted_slide_images(image_dir)


def export_pptx_to_images(pptx_path: Path, work_dir: Path) -> list[Path]:
    soffice = (
        shutil.which("soffice")
        or shutil.which("libreoffice")
        or next(
            (
                path
                for path in (
                    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
                    "/Applications/OpenOffice.app/Contents/MacOS/soffice",
                )
                if Path(path).exists()
            ),
            None,
        )
    )
    if not soffice:
        raise RuntimeError("LibreOffice/soffice is required to export PPTX slides to images")
    pdf_dir = work_dir / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(pdf_dir), str(pptx_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(f"soffice failed for {pptx_path}: {result.stderr or result.stdout}")
    candidates = sorted(pdf_dir.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise RuntimeError(f"soffice did not create a PDF for {pptx_path}")
    return export_pdf_to_images(candidates[0], work_dir / "pptx_pages")


def collect_slide_images(slide_source: Path, work_dir: Path) -> list[Path]:
    slide_source = slide_source.resolve()
    if slide_source.is_dir() or slide_source.suffix.lower() in IMAGE_EXTS:
        return sorted_slide_images(slide_source)
    suffix = slide_source.suffix.lower()
    if suffix == ".pdf":
        return export_pdf_to_images(slide_source, work_dir / "pdf_pages")
    if suffix in {".pptx", ".ppt"}:
        return export_pptx_to_images(slide_source, work_dir / "pptx_export")
    raise ValueError(f"unsupported slide source type: {slide_source}")


def ensure_file(path: Path, label: str) -> Path:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    if path.stat().st_size <= 0:
        raise ValueError(f"{label} is empty: {path}")
    return path.resolve()


def ensure_audio_file(path: Path) -> Path:
    audio = ensure_file(path, "audio")
    if audio.suffix.lower() not in AUDIO_EXTS:
        raise ValueError(f"unsupported audio type: {audio.suffix}. Expected one of {sorted(AUDIO_EXTS)}")
    return audio


def copy_ordered_slides(slides: Iterable[Path], slides_dir: Path) -> list[Path]:
    sources = [source.resolve() for source in slides]
    slides_dir.mkdir(parents=True, exist_ok=True)
    source_paths = set(sources)
    for stale in slides_dir.iterdir():
        if stale.resolve() in source_paths:
            continue
        if stale.is_file() and stale.name.startswith("slide_") and stale.suffix.lower() in IMAGE_EXTS:
            stale.unlink()
    copied: list[Path] = []
    for index, source in enumerate(sources, start=1):
        suffix = source.suffix.lower() if source.suffix else ".png"
        target = slides_dir / f"slide_{index:03d}{suffix}"
        if source != target.resolve():
            shutil.copy2(source, target)
        copied.append(target.resolve())
    return copied


def copy_asset(source: Path, target_dir: Path, target_name: str | None = None) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / (target_name or source.name)
    if source.resolve() != target.resolve():
        shutil.copy2(source, target)
    return target.resolve()


def parse_timestamp(value: str) -> float:
    value = value.replace(",", ".")
    parts = value.split(":")
    if len(parts) == 3:
        hours, minutes, seconds = parts
    elif len(parts) == 2:
        hours, minutes, seconds = "0", parts[0], parts[1]
    else:
        return 0.0
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def first_present(payload: dict[str, object], keys: Iterable[str]) -> object | None:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return None


def seconds_value(value: object, *, milliseconds: bool = False) -> float | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        if ":" in value:
            return parse_timestamp(value)
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        return None
    return seconds / 1000.0 if milliseconds else seconds


def cue_from_payload(payload: dict[str, object]) -> dict[str, object] | None:
    text = clean(str(first_present(payload, ("text", "sentence", "content", "caption", "word")) or ""))
    if not text:
        return None
    start = seconds_value(first_present(payload, ("start_ms", "begin_ms")), milliseconds=True)
    end = seconds_value(first_present(payload, ("end_ms", "finish_ms")), milliseconds=True)
    if start is None:
        start = seconds_value(first_present(payload, ("start", "begin", "start_time", "offset")))
    if end is None:
        end = seconds_value(first_present(payload, ("end", "finish", "end_time")))
    if end is None:
        duration = seconds_value(first_present(payload, ("duration", "duration_seconds")))
        end = (start or 0.0) + (duration or 2.5)
    start = start or 0.0
    if end <= start:
        end = start + 2.5
    return {"start": start, "end": end, "text": text}


def json_transcript_cues(payload: object) -> list[dict[str, object]]:
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = (
            payload.get("segments")
            or payload.get("captions")
            or payload.get("chunks")
            or payload.get("results")
            or payload.get("words")
            or []
        )
        if not items and payload.get("text"):
            items = [payload]
    else:
        items = []

    cues: list[dict[str, object]] = []
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                cue = cue_from_payload(item)
                if cue:
                    cues.append(cue)
    return cues


def chunk_caption_text(text: str, max_chars: int = 44) -> list[str]:
    text = clean(text)
    if len(text) <= max_chars:
        return [text] if text else []

    chunks: list[str] = []
    current = ""
    pieces = re.split(r"([。！？!?；;，,、])", text)
    for piece in pieces:
        if not piece:
            continue
        candidate = current + piece
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current.strip())
        current = piece.strip()
        while len(current) > max_chars:
            chunks.append(current[:max_chars].strip())
            current = current[max_chars:].strip()
    if current:
        chunks.append(current.strip())
    return [chunk for chunk in chunks if chunk]


def normalize_cues(cues: list[dict[str, object]]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for cue in sorted(cues, key=lambda item: (float(item["start"]), float(item["end"]))):
        text = clean(str(cue["text"]))
        if not text:
            continue
        start = float(cue["start"])
        end = max(float(cue["end"]), start + 0.8)
        chunks = chunk_caption_text(text)
        if len(chunks) == 1:
            normalized.append({"start": start, "end": end, "text": chunks[0]})
            continue
        total = max(end - start, len(chunks) * 0.8)
        per_chunk = total / len(chunks)
        for index, chunk in enumerate(chunks):
            chunk_start = start + per_chunk * index
            normalized.append({"start": chunk_start, "end": chunk_start + per_chunk, "text": chunk})
    return normalized


def parse_transcript(path: Path) -> list[dict[str, object]]:
    if not path or not path.exists():
        return []
    if path.suffix.lower() == ".json":
        try:
            return normalize_cues(json_transcript_cues(json.loads(path.read_text(encoding="utf-8", errors="ignore"))))
        except json.JSONDecodeError:
            return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    cues: list[dict[str, object]] = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if "-->" not in line:
            index += 1
            continue
        start_raw, end_raw = [part.strip().split()[0] for part in line.split("-->", 1)]
        index += 1
        text_lines: list[str] = []
        while index < len(lines) and lines[index].strip():
            text_lines.append(lines[index].strip())
            index += 1
        text = clean(" ".join(text_lines))
        if text:
            cues.append({"start": parse_timestamp(start_raw), "end": parse_timestamp(end_raw), "text": text})
    return normalize_cues(cues)


def transcript_duration(cues: list[dict[str, object]]) -> float:
    if not cues:
        return 0.0
    return max(float(cue["end"]) for cue in cues)


def audio_duration_seconds(audio: Path) -> float:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return 0.0
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        return 0.0
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def segment_slides(total_duration: float, slide_count: int) -> list[dict[str, float]]:
    if slide_count <= 0:
        return []
    duration = total_duration if total_duration > 0 else slide_count * DEFAULT_DURATION_PER_SLIDE
    per_slide = duration / slide_count
    return [{"start": index * per_slide, "duration": per_slide} for index in range(slide_count)]


def candidate_terms(text: str) -> list[str]:
    terms = re.findall(r"[A-Za-z][A-Za-z0-9+.-]{2,}|[\u4e00-\u9fff]{2,8}", text)
    banned = {"这个", "一个", "什么", "不是", "可以", "我们", "他们", "因为", "所以", "但是", "时候"}
    unique: list[str] = []
    for term in terms:
        if term in banned or term in unique:
            continue
        unique.append(term)
    return unique


def build_keyword_overlays(cues: list[dict[str, object]], slide_count: int) -> list[dict[str, object]]:
    overlays: list[dict[str, object]] = []
    if slide_count <= 0:
        return overlays
    for index, cue in enumerate(cues[: slide_count * 3]):
        terms = candidate_terms(str(cue["text"]))
        if not terms:
            continue
        slide = min(index // 3 + 1, slide_count)
        start = float(cue["start"])
        overlays.append({"text": terms[0], "start": start, "end": min(float(cue["end"]), start + 2.4), "slide": slide})
    return overlays


def write_design(project_dir: Path, title: str) -> Path:
    text = f"""# DESIGN

## Video Title

{title}

## Style Prompt

Strong narrative dynamic video built from premium PPT visuals and podcast audio. The output should feel like a high-end strategy documentary or polished AI explainer, not a static slide recording.

## Visual Rules

- 16:9 landscape, 1920x1080.
- Strong narrative motion only: multi-shot slide treatment, push-ins, pans, local crop/zoom emphasis, keyword overlays, and narrative transitions.
- Full captions plus sparse keyword emphasis overlays.
- Premium startup aesthetic: modern, restrained, business-class, slightly futuristic.
- Avoid flashy template effects, neon glow, equalizer bars, random motion, overcrowded subtitles, and static slide playback.
"""
    path = project_dir / "DESIGN.md"
    path.write_text(text, encoding="utf-8")
    return path


def render_index_html(
    *,
    title: str,
    slides: list[Path],
    audio: Path,
    transcript: Path | None,
    cues: list[dict[str, object]],
    keyword_overlays: list[dict[str, object]],
    project_dir: Path,
    duration: float,
) -> str:
    slide_segments = segment_slides(duration, len(slides))
    slide_payload = [
        {"src": rel(slide, project_dir), "start": segment["start"], "duration": segment["duration"], "index": index}
        for index, (slide, segment) in enumerate(zip(slides, slide_segments), start=1)
    ]
    data = {
        "slides": slide_payload,
        "cues": cues,
        "keywords": keyword_overlays,
        "duration": duration if duration > 0 else len(slides) * DEFAULT_DURATION_PER_SLIDE,
    }
    transcript_track = (
        f'<track kind="subtitles" src="{html.escape(rel(transcript, project_dir))}" srclang="zh" label="Chinese" default />'
        if transcript and transcript.suffix.lower() in {".srt", ".vtt"}
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <style>
    html, body {{
      margin: 0;
      width: 100%;
      height: 100%;
      background: #05070b;
      color: #f8fafc;
      font-family: sans-serif;
      overflow: hidden;
    }}
    #ppt-podcast-video {{
      position: relative;
      width: 1920px;
      height: 1080px;
      overflow: hidden;
      background: #05070b;
    }}
    .stage {{
      position: absolute;
      inset: 0;
      overflow: hidden;
    }}
    .slide-shot {{
      position: absolute;
      inset: 0;
      opacity: 0;
      transform-origin: center center;
      will-change: transform, opacity, filter;
    }}
    .slide-shot img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      filter: saturate(0.92) contrast(1.03);
    }}
    .vignette {{
      position: absolute;
      inset: 0;
      background: radial-gradient(circle at 68% 28%, rgba(148, 163, 184, 0.14), transparent 34%),
                  linear-gradient(90deg, rgba(2, 6, 23, 0.45), transparent 38%, rgba(2, 6, 23, 0.38));
      pointer-events: none;
      z-index: 5;
    }}
    .caption {{
      position: absolute;
      left: 180px;
      right: 180px;
      bottom: 86px;
      min-height: 72px;
      display: flex;
      align-items: center;
      justify-content: center;
      text-align: center;
      font-size: 34px;
      line-height: 1.45;
      font-weight: 400;
      letter-spacing: 0;
      color: #f8fafc;
      text-shadow: 0 2px 16px rgba(0,0,0,.45);
      z-index: 20;
    }}
    .keyword {{
      position: absolute;
      top: 118px;
      right: 150px;
      padding: 14px 22px;
      border: 1px solid rgba(226, 232, 240, 0.34);
      color: #e2e8f0;
      font-size: 28px;
      line-height: 1;
      font-weight: 300;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      background: rgba(15, 23, 42, 0.34);
      backdrop-filter: blur(12px);
      opacity: 0;
      z-index: 22;
    }}
    .route-line {{
      position: absolute;
      left: 132px;
      top: 132px;
      width: 1px;
      height: 816px;
      background: linear-gradient(to bottom, transparent, rgba(226,232,240,.46), transparent);
      opacity: .42;
      z-index: 10;
    }}
    .title-mark {{
      position: absolute;
      left: 160px;
      top: 108px;
      font-size: 18px;
      line-height: 1;
      color: rgba(226,232,240,.7);
      letter-spacing: .18em;
      text-transform: uppercase;
      z-index: 21;
    }}
  </style>
</head>
<body>
  <div id="ppt-podcast-video" data-composition-id="ppt-podcast-video" data-start="0" data-duration="{data['duration']:.3f}" data-width="1920" data-height="1080">
    <div class="stage" id="stage" data-layout-allow-overflow></div>
    <div class="vignette"></div>
    <div class="route-line"></div>
    <div class="title-mark">{html.escape(title)}</div>
    <div class="keyword" id="keyword"></div>
    <div class="caption" id="caption"></div>
    <audio id="podcast-audio" data-start="0" data-duration="{data['duration']:.3f}" data-track-index="2" src="{html.escape(rel(audio, project_dir))}" data-volume="1">
      {transcript_track}
    </audio>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <script>
    window.__timelines = window.__timelines || {{}};
    var DATA = {json.dumps(data, ensure_ascii=False)};
    var stage = document.getElementById("stage");
    DATA.slides.forEach(function (slide) {{
      var wrap = document.createElement("div");
      wrap.className = "slide-shot";
      wrap.id = "slide-" + slide.index;
      var img = document.createElement("img");
      img.src = slide.src;
      img.alt = "slide " + slide.index;
      wrap.appendChild(img);
      stage.appendChild(wrap);
    }});

    var caption = document.getElementById("caption");
    var keyword = document.getElementById("keyword");
    var tl = gsap.timeline({{ paused: true }});

    DATA.slides.forEach(function (slide, i) {{
      var el = "#slide-" + slide.index;
      var start = slide.start;
      var dur = slide.duration;
      var direction = i % 3;
      tl.set(el, {{ opacity: 1, scale: 1.03, x: direction === 0 ? -26 : 26, y: direction === 2 ? -18 : 0 }}, start);
      tl.to(el, {{
        scale: 1.16,
        x: direction === 0 ? 34 : direction === 1 ? -34 : 0,
        y: direction === 2 ? 22 : -8,
        duration: Math.max(dur - 0.7, 0.5),
        ease: "none"
      }}, start);
      tl.to(el, {{ opacity: 0, duration: 0.42, ease: "power2.inOut" }}, start + Math.max(dur - 0.42, 0));
    }});

    DATA.cues.forEach(function (cue) {{
      tl.set(caption, {{ textContent: cue.text }}, cue.start);
      tl.fromTo(caption, {{ opacity: 0, y: 16 }}, {{ opacity: 1, y: 0, duration: 0.22, ease: "power2.out" }}, cue.start);
      tl.to(caption, {{ opacity: 0, y: -10, duration: 0.22, ease: "power2.in" }}, Math.max(cue.end - 0.22, cue.start + 0.3));
    }});

    DATA.keywords.forEach(function (item) {{
      tl.set(keyword, {{ textContent: item.text }}, item.start);
      tl.fromTo(keyword, {{ opacity: 0, y: -12, scale: 0.98 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.28, ease: "power3.out" }}, item.start);
      tl.to(keyword, {{ opacity: 0, y: 8, duration: 0.28, ease: "power2.in" }}, Math.max(item.end - 0.28, item.start + 0.5));
    }});

    window.__timelines["ppt-podcast-video"] = tl;
  </script>
</body>
</html>
"""


def build_manifest(
    *,
    status: str,
    output_dir: Path,
    stem: str,
    audio: Path,
    slide_source: Path,
    slides_dir: Path,
    slide_count: int,
    transcript: Path | None,
    keyword_overlays: list[dict[str, object]],
    project_dir: Path,
    output_video: Path,
    render_command: list[str],
    command_logs: list[dict[str, object]] | None = None,
    error: str | None = None,
    failed_step: str | None = None,
    diagnostic_log: str | None = None,
) -> dict[str, object]:
    manifest: dict[str, object] = {
        "status": status,
        "mode": "ppt_podcast_video",
        "style": "strong_narrative_dynamic",
        "aspect_ratio": "16:9",
        "audio": str(audio),
        "slide_source": str(slide_source),
        "slides_dir": str(slides_dir),
        "slide_count": slide_count,
        "transcript": str(transcript) if transcript else "",
        "keyword_overlays": keyword_overlays,
        "hyperframes_project": str(project_dir),
        "output_video": str(output_video),
        "render_command": " ".join(render_command),
        "output_dir": str(output_dir),
        "stem": stem,
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    if command_logs is not None:
        manifest["command_logs"] = command_logs
    if error:
        manifest["error"] = error
    if failed_step:
        manifest["failed_step"] = failed_step
    if diagnostic_log:
        manifest["diagnostic_log"] = diagnostic_log
    return manifest


def run_command(cmd: list[str], cwd: Path) -> CommandResult:
    result = subprocess.run(cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return CommandResult(result.returncode, result.stdout, result.stderr)


def newest_transcript_file(root: Path, before: set[Path]) -> Path | None:
    candidates = [
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".json", ".srt", ".vtt"} and path.resolve() not in before
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0].resolve()


def run_hyperframes_transcribe(
    project_dir: Path,
    audio: Path,
    *,
    run_command: Callable[[list[str], Path], CommandResult] = run_command,
) -> tuple[Path, dict[str, object]]:
    before = {path.resolve() for path in project_dir.rglob("*") if path.is_file()}
    cmd = ["npx", "hyperframes", "transcribe", str(audio)]
    result = run_command(cmd, project_dir)
    log = {"cmd": cmd, "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    if result.returncode != 0:
        raise HyperFramesCommandError(f"HyperFrames transcription failed: {result.stderr or result.stdout}", [log])
    transcript = newest_transcript_file(project_dir, before)
    if not transcript:
        paths = re.findall(r"(/[^\s]+\.(?:json|srt|vtt)|[A-Za-z0-9_./-]+\.(?:json|srt|vtt))", result.stdout + "\n" + result.stderr)
        for raw in paths:
            candidate = (project_dir / raw).resolve() if not raw.startswith("/") else Path(raw).resolve()
            if candidate.exists():
                transcript = candidate
                break
    if not transcript:
        raise HyperFramesCommandError("HyperFrames transcription completed but no transcript file was found", [log])
    return transcript, log


def run_hyperframes_render(
    project_dir: Path,
    output_video: Path,
    *,
    quality: str = "standard",
    fps: int = 30,
    run_command: Callable[[list[str], Path], CommandResult] = run_command,
) -> list[dict[str, object]]:
    output_video.parent.mkdir(parents=True, exist_ok=True)
    commands = [
        ["npx", "hyperframes", "lint"],
        ["npx", "hyperframes", "inspect"],
        ["npx", "hyperframes", "render", "--output", str(output_video), "--quality", quality, "--fps", str(fps)],
    ]
    logs: list[dict[str, object]] = []
    for cmd in commands:
        result = run_command(cmd, project_dir)
        logs.append({"cmd": cmd, "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode != 0:
            doctor = run_command(["npx", "hyperframes", "doctor"], project_dir)
            logs.append({"cmd": ["npx", "hyperframes", "doctor"], "returncode": doctor.returncode, "stdout": doctor.stdout, "stderr": doctor.stderr})
            raise HyperFramesCommandError(f"HyperFrames command failed: {' '.join(cmd)}", logs)
    if not output_video.exists() or output_video.stat().st_size <= 0:
        raise HyperFramesCommandError(f"HyperFrames render did not create a non-empty MP4: {output_video}", logs)
    return logs


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_pipeline(
    *,
    slide_source: Path,
    audio: Path,
    output_dir: Path,
    stem: str,
    transcript: Path | None = None,
    title: str = "PPT Podcast Video",
    no_render: bool = False,
    quality: str = "standard",
    fps: int = 30,
    emit_json: bool = True,
) -> dict[str, object]:
    audio = ensure_audio_file(Path(audio))
    slide_source = Path(slide_source).resolve()
    output_dir = Path(output_dir).resolve()
    slides_dir = output_dir / f"{stem}_slides"
    project_dir = output_dir / f"{stem}_video_project"
    slide_work_dir = project_dir / ".slide_export_work"
    assets_dir = project_dir / "assets"
    output_video = output_dir / f"{stem}_video.mp4"
    manifest_path = output_dir / f"{stem}_video_manifest.json"

    project_dir.mkdir(parents=True, exist_ok=True)
    source_slides = collect_slide_images(slide_source, slide_work_dir)
    copied_slides = copy_ordered_slides(source_slides, slides_dir)
    project_slides = copy_ordered_slides(copied_slides, assets_dir / "slides")
    copied_audio = copy_asset(audio, assets_dir, audio.name)
    command_logs: list[dict[str, object]] = []
    copied_transcript = copy_asset(Path(transcript).resolve(), assets_dir, Path(transcript).name) if transcript else None
    if copied_transcript is None and not no_render:
        try:
            generated_transcript, transcribe_log = run_hyperframes_transcribe(project_dir, copied_audio)
            command_logs.append(transcribe_log)
            copied_transcript = copy_asset(generated_transcript, assets_dir, generated_transcript.name)
        except Exception as exc:
            if isinstance(exc, HyperFramesCommandError):
                command_logs.extend(exc.logs)
            manifest = build_manifest(
                status="failed",
                output_dir=output_dir,
                stem=stem,
                audio=copied_audio,
                slide_source=slide_source,
                slides_dir=slides_dir,
                slide_count=len(copied_slides),
                transcript=None,
                keyword_overlays=[],
                project_dir=project_dir,
                output_video=output_video,
                render_command=[],
                command_logs=command_logs,
                error=str(exc),
                failed_step="hyperframes_transcribe",
                diagnostic_log=json.dumps(command_logs, ensure_ascii=False),
            )
            write_json(manifest_path, manifest)
            raise RuntimeError(f"video transcription failed; manifest written to {manifest_path}: {exc}") from exc
    cues = parse_transcript(copied_transcript) if copied_transcript else []
    duration = transcript_duration(cues) or audio_duration_seconds(copied_audio) or len(copied_slides) * DEFAULT_DURATION_PER_SLIDE
    keyword_overlays = build_keyword_overlays(cues, len(copied_slides))

    write_design(project_dir, title)
    html_text = render_index_html(
        title=title,
        slides=project_slides,
        audio=copied_audio,
        transcript=copied_transcript,
        cues=cues,
        keyword_overlays=keyword_overlays,
        project_dir=project_dir,
        duration=duration,
    )
    (project_dir / "index.html").write_text(html_text, encoding="utf-8")

    render_cmd = ["npx", "hyperframes", "render", "--output", str(output_video), "--quality", quality, "--fps", str(fps)]
    status = "project_ready" if no_render else "complete"
    error = failed_step = diagnostic_log = None
    if not no_render:
        try:
            render_logs = run_hyperframes_render(project_dir, output_video, quality=quality, fps=fps)
            command_logs.extend(render_logs)
        except Exception as exc:
            if isinstance(exc, HyperFramesCommandError):
                command_logs.extend(exc.logs)
            status = "failed"
            error = str(exc)
            failed_step = "hyperframes_render"
            diagnostic_log = json.dumps(command_logs, ensure_ascii=False)

    manifest = build_manifest(
        status=status,
        output_dir=output_dir,
        stem=stem,
        audio=copied_audio,
        slide_source=slide_source,
        slides_dir=slides_dir,
        slide_count=len(copied_slides),
        transcript=copied_transcript,
        keyword_overlays=keyword_overlays,
        project_dir=project_dir,
        output_video=output_video,
        render_command=render_cmd,
        command_logs=command_logs,
        error=error,
        failed_step=failed_step,
        diagnostic_log=diagnostic_log,
    )
    write_json(manifest_path, manifest)
    if status == "failed":
        raise RuntimeError(f"video render failed; manifest written to {manifest_path}: {error}")
    if emit_json:
        print(json.dumps({"manifest": str(manifest_path), "project": str(project_dir), "video": str(output_video), "status": status}, ensure_ascii=False, indent=2))
    return {"manifest": str(manifest_path), "project": str(project_dir), "video": str(output_video), "status": status}


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a HyperFrames dynamic video from PPT slide images and podcast audio.")
    parser.add_argument("--slides-source", required=True, help="Ordered slide images directory, one image, PDF, PPT, or PPTX.")
    parser.add_argument("--audio", required=True, help="Podcast audio path.")
    parser.add_argument("--output-dir", required=True, help="Output directory.")
    parser.add_argument("--stem", default="ppt_podcast_video", help="Output filename stem.")
    parser.add_argument("--transcript", help="Existing SRT/VTT/JSON transcript path.")
    parser.add_argument("--title", default="PPT Podcast Video", help="Video title.")
    parser.add_argument("--quality", default="standard", choices=["draft", "standard", "high"])
    parser.add_argument("--fps", default=30, type=int)
    parser.add_argument("--no-render", action="store_true", help="Only create project, manifest, and assets; skip HyperFrames render.")
    args = parser.parse_args()

    run_pipeline(
        slide_source=Path(args.slides_source),
        audio=Path(args.audio),
        output_dir=Path(args.output_dir),
        stem=args.stem,
        transcript=Path(args.transcript) if args.transcript else None,
        title=args.title,
        no_render=args.no_render,
        quality=args.quality,
        fps=args.fps,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
