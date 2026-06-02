#!/usr/bin/env python3
"""Generate NotebookLM non-audio artifacts through the nlm CLI.

This is the background entrypoint for slide decks, mind maps, and text-based
study artifacts. It keeps NotebookLM work in the CLI path and writes state/log
files that can be inspected without opening a browser.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)

TEXT_ACTIONS = {
    "summary": "summarize",
    "outline": "outline",
    "faq": "faq",
    "study-guide": "study-guide",
    "briefing-doc": "briefing-doc",
    "timeline": "timeline",
    "toc": "toc",
}

SLIDES_DESIGN_PROMPT = """你是一位专业的 PPT 设计师，同时也是内容提炼与视觉叙事专家。
用户提供原始内容后，你自主完成内容理解、结构设计和视觉决策，无需询问用户。

请基于 notebook 中的全部资料生成一份中文 PPT 设计稿。每一页必须按以下顺序输出：
1. 理解与决策结果
2. 中文版提示词
3. English Prompt

第一步：理解与决策。每页都要判断：
- 核心主题：这一页最核心要传达什么。
- 叙事结构：选择最合适的结构，例如大标题+金句、要点列表、数据呈现、对比、时间线、纯视觉封面等。优先用文字和排版表达逻辑。
- 视觉方向：根据内容气质决定配色、背景氛围、是否需要视觉装饰元素。
- 页面类型：封面页 / 内容页 / 结束页。
- 分享人：从输入中识别，未提及则留空，且不要显示“分享人”标签。
- 时间：固定为 2026-05-25，除非用户明确指定。

第二步：生成图像提示词。基于决策构建最适合的幻灯片图像提示词，整体风格保持一致，同时输出中文版和英文版。

不可变设计标准：
- 风格基调：优雅、极简、现代，高级初创企业美学，对标 Apple / Linear / Notion 的品牌视觉质感。
- 背景：根据内容气质自主选择深色系或浅色系，允许极克制的半透明几何形、极淡网格、微妙光影渐变。
- 禁止：粉色、紫色、彩虹渐变、暖橙、感性鲜艳色调、彩色填充色块、装饰性分割线、渐变文字、发光效果、阴影堆叠、文字水印、低质纹理。
- 配色：全页不超过 3 种颜色，强调色仅用于点缀，禁止用颜色区分内容模块。
- 排版：精致无衬线字体，Thin / Light / Regular 为主；主标题大字号轻字重，层级通过字号、字重、间距自然表达；留白占页面 40%-60%。
- 图形元素：全页合计不超过 3 个，必须高度克制。允许极细单色线条图标、极细引导箭头、极简节点结构图、细描边全大写标签。
- 禁止图形：彩色图标、圆形背景图标、粗箭头、彩色流程图、填色卡片、Infographic 风格。
- 视觉氛围：business-class premium, strategy deck quality, slightly futuristic but highly professional。
- 技术规格：16:9，语言默认中文优先，专有名词保留原文。
- 分享人与时间仅出现在封面页和结束页。

输出要求：
- 多页内容按页分别输出。
- 用 --- 分隔每一页。
- 每页必须包含：核心主题、叙事结构、视觉方向、页面类型、分享人、时间、中文版提示词、English Prompt。
- 这是一份可用于渲染真实 PPTX 的设计源稿，不要只输出普通要点大纲。"""

CHAT_PROMPTS = {
    "slides": SLIDES_DESIGN_PROMPT,
    "quiz": "基于 notebook 中的全部资料生成一份中文 Quiz，包含题目、选项、答案和简短解析。",
    "flashcards": "基于 notebook 中的全部资料生成中文记忆闪卡，使用 Markdown 表格：正面、背面、关键词。",
    "infographic": "基于 notebook 中的全部资料生成一份中文信息图文案蓝图，包含标题、模块、核心数据、视觉层级和图表建议。",
    "data-table": "基于 notebook 中的全部资料整理一张中文 Markdown 数据表，包含关键实体、观点、证据、来源线索和备注。",
    "mindmap": "基于 notebook 中的全部资料生成中文 Markdown 思维导图。使用分级标题和缩进项目符号表达主题、分支、关键关系和证据线索。",
    "summary": "基于 notebook 中的全部资料生成中文总结，突出核心观点、结构和可执行结论。",
    "outline": "基于 notebook 中的全部资料生成中文大纲，使用清晰层级组织主题、论点和支撑材料。",
    "faq": "基于 notebook 中的全部资料生成中文 FAQ，包含问题和简洁答案。",
    "study-guide": "基于 notebook 中的全部资料生成中文学习指南，包含关键概念、解释、复习重点和练习题。",
    "briefing-doc": "基于 notebook 中的全部资料生成中文简报文档，包含背景、核心发现、风险和建议。",
    "timeline": "基于 notebook 中的全部资料生成中文时间线，按时间顺序列出事件和意义。",
    "toc": "基于 notebook 中的全部资料生成中文目录/结构表，体现内容层级。",
}


def run(
    cmd: list[str],
    *,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
        )
    return result


def is_transient_output(text: str) -> bool:
    lowered = text.lower()
    needles = [
        "tls handshake timeout",
        "timeout",
        "connection reset",
        "connection refused",
        "temporarily unavailable",
        "too many requests",
        "rate limit",
        " 5xx",
        "exit-class=transient",
    ]
    return any(needle in lowered for needle in needles)


def run_retry(
    cmd: list[str],
    *,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
    attempts: int = 3,
    sleep_seconds: int = 5,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    last = None
    for attempt in range(1, attempts + 1):
        last = run(cmd, env=env, input_text=input_text)
        if last.returncode == 0:
            return last
        combined = f"{last.stdout}\n{last.stderr}"
        if attempt == attempts or not is_transient_output(combined):
            break
        time.sleep(sleep_seconds * attempt)
    assert last is not None
    if check and last.returncode != 0:
        raise RuntimeError(
            f"command failed ({last.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{last.stdout}\n\nstderr:\n{last.stderr}"
        )
    return last


def find_nlm(auto_install: bool) -> str:
    candidates = [
        shutil.which("nlm"),
        str(Path.home() / "go" / "bin" / "nlm"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate

    if not auto_install:
        raise SystemExit("nlm CLI not found. Install it or pass --install-nlm.")

    go = shutil.which("go")
    if not go:
        raise SystemExit("Go is required to install nlm. Install Go first.")

    install = run([go, "install", "github.com/tmc/nlm/cmd/nlm@latest"])
    if install.returncode != 0:
        raise SystemExit(install.stderr or install.stdout)

    installed = Path.home() / "go" / "bin" / "nlm"
    if not installed.exists():
        raise SystemExit("nlm install completed but binary was not found in ~/go/bin.")
    return str(installed)


def env_with_authuser(authuser: str | None) -> dict[str, str]:
    env = os.environ.copy()
    if authuser:
        env["NLM_AUTHUSER"] = authuser
    return env


def ensure_auth(nlm: str, env: dict[str, str], profile: str | None) -> None:
    probe = run_retry([nlm, "notebook", "list", "--limit", "1"], env=env)
    if probe.returncode == 0:
        return
    if "Authentication required" not in probe.stderr and "authentication required" not in probe.stderr:
        raise RuntimeError(probe.stderr or probe.stdout)

    cmd = [nlm, "auth"]
    if profile:
        cmd.append(profile)
    auth = run(cmd, env=env)
    if auth.returncode != 0:
        raise RuntimeError(auth.stderr or auth.stdout)

    verify = run_retry([nlm, "notebook", "list", "--limit", "1"], env=env)
    if verify.returncode != 0:
        raise RuntimeError(verify.stderr or verify.stdout)


def first_uuid(text: str) -> str:
    match = UUID_RE.search(text)
    if not match:
        raise RuntimeError(f"could not parse id from output:\n{text}")
    return match.group(0)


def create_notebook(nlm: str, env: dict[str, str], title: str) -> str:
    result = run_retry([nlm, "notebook", "create", title], env=env, check=True)
    return first_uuid(result.stdout + "\n" + result.stderr)


def add_source(nlm: str, env: dict[str, str], notebook_id: str, source: str, title: str) -> None:
    source_path = Path(source).expanduser()
    if source_path.exists():
        run_retry([nlm, "source", "add", "--name", title, notebook_id, str(source_path)], env=env, check=True)
        return

    if source.startswith(("http://", "https://")):
        run_retry([nlm, "source", "add", "--name", title, notebook_id, source], env=env, check=True)
        return

    run_retry(
        [nlm, "source", "add", "--name", title, "--mime", "text/markdown", notebook_id, "-"],
        env=env,
        input_text=source,
        check=True,
    )


def list_source_ids(nlm: str, env: dict[str, str], notebook_id: str) -> list[str]:
    result = run_retry([nlm, "--json", "source", "list", notebook_id], env=env, check=True)
    ids: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        source_id = rec.get("source_id")
        if source_id:
            ids.append(source_id)
    if not ids:
        raise RuntimeError("no source ids found after adding sources")
    return ids


def list_artifacts(nlm: str, env: dict[str, str], notebook_id: str) -> list[dict[str, object]]:
    result = run_retry([nlm, "--json", "artifact", "list", notebook_id], env=env, attempts=2, check=True)
    records: list[dict[str, object]] = []
    for line in result.stdout.splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def artifact_is_ready(record: dict[str, object]) -> bool:
    state = str(record.get("state", "")).upper()
    return state.endswith("READY") or state.endswith("DONE") or state.endswith("COMPLETE") or state == "READY"


def newest_ready_artifact(
    nlm: str,
    env: dict[str, str],
    notebook_id: str,
    type_hint: str,
    timeout_seconds: int,
    poll_seconds: int,
) -> dict[str, object]:
    deadline = time.monotonic() + timeout_seconds
    last: list[dict[str, object]] = []
    while time.monotonic() < deadline:
        last = list_artifacts(nlm, env, notebook_id)
        candidates = [
            rec
            for rec in last
            if type_hint.upper() in str(rec.get("type", "")).upper() and artifact_is_ready(rec)
        ]
        if candidates:
            return candidates[-1]
        time.sleep(poll_seconds)
    raise TimeoutError(f"artifact did not become ready. Last artifacts: {json.dumps(last, ensure_ascii=False)}")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_state(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def create_slides(
    nlm: str,
    env: dict[str, str],
    notebook_id: str,
    instructions: str,
    output_dir: Path,
    stem: str,
    timeout_seconds: int,
    poll_seconds: int,
) -> dict[str, object]:
    result = run_retry([nlm, "create-slides", notebook_id, instructions], env=env)
    if result.returncode not in {0, 7}:
        fallback_prompt = instructions or CHAT_PROMPTS["slides"]
        if instructions and instructions != CHAT_PROMPTS["slides"]:
            fallback_prompt = f"{CHAT_PROMPTS['slides']}\n\n额外要求：{instructions}"
        fallback = run_retry([nlm, "generate-chat", notebook_id, fallback_prompt], env=env, check=True)
        out = output_dir / f"{stem}_slides.md"
        write_text(out, fallback.stdout)
        return {
            "slides_markdown": str(out),
            "method": "generate-chat fallback after nlm create-slides failed",
            "native_error": (result.stderr or result.stdout).strip(),
        }
    artifact = newest_ready_artifact(nlm, env, notebook_id, "SLIDE", timeout_seconds, poll_seconds)
    artifact_id = str(artifact["artifact_id"])
    details = run_retry([nlm, "artifact", "get", artifact_id], env=env, check=True)
    out = output_dir / f"{stem}_slides_artifact.txt"
    write_text(out, details.stdout)
    return {"artifact_id": artifact_id, "artifact_details": str(out), "artifact": artifact, "method": "nlm create-slides"}


def create_mindmap(
    nlm: str,
    env: dict[str, str],
    notebook_id: str,
    source_ids: list[str],
    output_dir: Path,
    stem: str,
) -> dict[str, object]:
    result = run_retry([nlm, "mindmap", notebook_id, *source_ids], env=env)
    out = output_dir / f"{stem}_mindmap.md"
    if result.returncode != 0:
        fallback = run_retry([nlm, "generate-chat", notebook_id, CHAT_PROMPTS["mindmap"]], env=env, check=True)
        write_text(out, fallback.stdout)
        return {
            "mindmap": str(out),
            "source_ids": source_ids,
            "method": "generate-chat fallback after nlm mindmap failed",
            "native_error": (result.stderr or result.stdout).strip(),
        }
    body = result.stdout.strip()
    if not body:
        body = "Mindmap generated by NotebookLM and saved as a note in the notebook.\n"
    write_text(out, body + "\n")
    return {"mindmap": str(out), "source_ids": source_ids, "method": "nlm mindmap"}


def create_video(
    nlm: str,
    env: dict[str, str],
    notebook_id: str,
    instructions: str,
    output_dir: Path,
    stem: str,
    timeout_seconds: int,
    poll_seconds: int,
) -> dict[str, object]:
    result = run_retry([nlm, "create-video", notebook_id, instructions], env=env)
    if result.returncode not in {0, 7}:
        raise RuntimeError(result.stderr or result.stdout)
    video_path = output_dir / f"{stem}.mp4"
    deadline = time.monotonic() + timeout_seconds
    last_error = ""
    while time.monotonic() < deadline:
        if video_path.exists():
            video_path.unlink()
        download = run_retry([nlm, "video", "download", notebook_id, str(video_path)], env=env, attempts=2)
        if download.returncode == 0 and video_path.exists() and video_path.stat().st_size > 0:
            return {"video": str(video_path), "video_size": video_path.stat().st_size}
        last_error = (download.stderr or download.stdout).strip()
        time.sleep(poll_seconds)
    raise TimeoutError(f"video download did not become ready. Last output: {last_error}")


def create_report(
    nlm: str,
    env: dict[str, str],
    notebook_id: str,
    report_type: str,
    instructions: str,
    output_dir: Path,
    stem: str,
    timeout_seconds: int,
    poll_seconds: int,
) -> dict[str, object]:
    result = run_retry([nlm, "create-report", notebook_id, report_type, instructions], env=env)
    if result.returncode not in {0, 7}:
        raise RuntimeError(result.stderr or result.stdout)
    artifact = newest_ready_artifact(nlm, env, notebook_id, "REPORT", timeout_seconds, poll_seconds)
    artifact_id = str(artifact["artifact_id"])
    details = run_retry([nlm, "artifact", "get", artifact_id], env=env, check=True)
    out = output_dir / f"{stem}_report.md"
    write_text(out, details.stdout)
    return {"artifact_id": artifact_id, "report": str(out), "artifact": artifact}


def create_text_action(
    nlm: str,
    env: dict[str, str],
    kind: str,
    notebook_id: str,
    source_ids: list[str],
    output_dir: Path,
    stem: str,
) -> dict[str, object]:
    command = TEXT_ACTIONS[kind]
    out = output_dir / f"{stem}_{kind}.md"
    result = run_retry([nlm, command, notebook_id, *source_ids], env=env)
    if result.returncode != 0:
        fallback = run_retry([nlm, "generate-chat", notebook_id, CHAT_PROMPTS[kind]], env=env, check=True)
        write_text(out, fallback.stdout)
        return {
            kind.replace("-", "_"): str(out),
            "source_ids": source_ids,
            "method": f"generate-chat fallback after nlm {command} failed",
            "native_error": (result.stderr or result.stdout).strip(),
        }
    write_text(out, result.stdout)
    return {kind.replace("-", "_"): str(out), "source_ids": source_ids, "method": f"nlm {command}"}


def create_chat_artifact(
    nlm: str,
    env: dict[str, str],
    kind: str,
    notebook_id: str,
    instructions: str,
    output_dir: Path,
    stem: str,
) -> dict[str, object]:
    prompt = instructions if instructions else CHAT_PROMPTS[kind]
    result = run_retry([nlm, "generate-chat", notebook_id, prompt], env=env, check=True)
    out = output_dir / f"{stem}_{kind}.md"
    write_text(out, result.stdout)
    return {kind.replace("-", "_"): str(out), "method": "generate-chat"}


def spawn_background(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / f"{args.stem}.notebooklm-artifact.log"
    state_path = output_dir / f"{args.stem}.notebooklm-artifact.state.json"

    cmd = [sys.executable, str(Path(__file__).resolve())]
    for key, value in vars(args).items():
        if key == "background" or value is None or value is False:
            continue
        flag = "--" + key.replace("_", "-")
        if isinstance(value, list):
            for item in value:
                cmd.extend([flag, str(item)])
        elif value is True:
            cmd.append(flag)
        else:
            cmd.extend([flag, str(value)])

    with log_path.open("ab") as log:
        proc = subprocess.Popen(
            cmd,
            stdout=log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )

    write_state(
        state_path,
        {
            "status": "running",
            "pid": proc.pid,
            "log": str(log_path),
            "output_dir": str(output_dir),
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        },
    )
    print(json.dumps({"pid": proc.pid, "log": str(log_path), "state": str(state_path)}, ensure_ascii=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate NotebookLM artifacts via nlm.")
    parser.add_argument("--source", action="append", required=True, help="Local file, URL, or literal text source. Repeat for multiple sources.")
    parser.add_argument("--output-dir", required=True, help="Artifact output directory.")
    parser.add_argument("--title", required=True, help="Notebook title.")
    parser.add_argument("--source-title", help="Source title prefix. Defaults to --title.")
    parser.add_argument("--stem", default="notebooklm_artifact", help="Output filename stem.")
    parser.add_argument(
        "--kind",
        required=True,
        choices=[
            "slides",
            "mindmap",
            "video",
            "report",
            "summary",
            "outline",
            "faq",
            "study-guide",
            "briefing-doc",
            "timeline",
            "toc",
            "quiz",
            "flashcards",
            "infographic",
            "data-table",
        ],
    )
    parser.add_argument("--instructions", default="", help="Generation instructions.")
    parser.add_argument("--report-type", default="briefing_doc", help="Report type for nlm create-report.")
    parser.add_argument("--auth-profile", help="Browser profile name/path for nlm auth, e.g. Oje or 'Profile 9'.")
    parser.add_argument("--authuser", help="NLM_AUTHUSER value for multi-account profiles.")
    parser.add_argument("--nlm", help="Path to nlm binary.")
    parser.add_argument("--install-nlm", action="store_true", help="Install nlm with go install if missing.")
    parser.add_argument("--background", action="store_true", help="Detach and run in the background.")
    parser.add_argument("--timeout-minutes", type=int, default=20)
    parser.add_argument("--poll-seconds", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.background:
        spawn_background(args)
        return 0

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = output_dir / f"{args.stem}.notebooklm-artifact.state.json"

    payload: dict[str, object] = {
        "status": "starting",
        "kind": args.kind,
        "output_dir": str(output_dir),
    }
    write_state(state_path, payload)

    try:
        nlm = args.nlm or find_nlm(args.install_nlm)
        env = env_with_authuser(args.authuser)
        ensure_auth(nlm, env, args.auth_profile)

        notebook_id = create_notebook(nlm, env, args.title)
        payload.update({"status": "notebook_created", "notebook_id": notebook_id})
        write_state(state_path, payload)

        for index, source in enumerate(args.source, start=1):
            title = args.source_title or args.title
            if len(args.source) > 1:
                title = f"{title} {index}"
            add_source(nlm, env, notebook_id, source, title)
        source_ids = list_source_ids(nlm, env, notebook_id)
        payload.update({"status": "sources_added", "source_ids": source_ids})
        write_state(state_path, payload)

        instructions = args.instructions or {
            "slides": CHAT_PROMPTS["slides"],
            "mindmap": "Create a Chinese mind map that preserves the source structure and key relationships.",
            "video": "Create a concise Chinese video overview.",
            "report": "Create a structured Chinese report.",
        }.get(args.kind, "")

        if args.kind == "slides":
            payload["status"] = "slides_generating"
            write_state(state_path, payload)
            result = create_slides(nlm, env, notebook_id, instructions, output_dir, args.stem, args.timeout_minutes * 60, args.poll_seconds)
        elif args.kind == "mindmap":
            payload["status"] = "mindmap_generating"
            write_state(state_path, payload)
            result = create_mindmap(nlm, env, notebook_id, source_ids, output_dir, args.stem)
        elif args.kind == "video":
            payload["status"] = "video_generating"
            write_state(state_path, payload)
            result = create_video(nlm, env, notebook_id, instructions, output_dir, args.stem, args.timeout_minutes * 60, args.poll_seconds)
        elif args.kind == "report":
            payload["status"] = "report_generating"
            write_state(state_path, payload)
            result = create_report(nlm, env, notebook_id, args.report_type, instructions, output_dir, args.stem, args.timeout_minutes * 60, args.poll_seconds)
        elif args.kind in TEXT_ACTIONS:
            payload["status"] = f"{args.kind}_generating"
            write_state(state_path, payload)
            result = create_text_action(nlm, env, args.kind, notebook_id, source_ids, output_dir, args.stem)
        else:
            payload["status"] = f"{args.kind}_generating"
            write_state(state_path, payload)
            result = create_chat_artifact(nlm, env, args.kind, notebook_id, instructions, output_dir, args.stem)

        payload.update(
            {
                "status": "complete",
                "completed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                **result,
            }
        )
        write_state(state_path, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        payload.update({"status": "failed", "error": str(exc)})
        write_state(state_path, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
