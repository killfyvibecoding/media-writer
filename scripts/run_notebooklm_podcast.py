#!/usr/bin/env python3
"""Run NotebookLM podcast generation through the nlm CLI.

This script is the preferred background entrypoint for the media-writer
podcast layer. It avoids UI automation once NotebookLM CLI authentication is
available.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
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


@dataclass(frozen=True)
class RuntimePaths:
    audio_path: Path
    state_path: Path
    log_path: Path


def runtime_paths(output_dir: Path, stem: str, runtime_dir: Path | None = None) -> RuntimePaths:
    output_dir = output_dir.expanduser().resolve()
    if runtime_dir is None:
        runtime_dir = output_dir.parent / ".media-writer-runtime" / output_dir.name
    runtime_dir = runtime_dir.expanduser().resolve()
    return RuntimePaths(
        audio_path=output_dir / f"{stem}.m4a",
        state_path=runtime_dir / f"{stem}.notebooklm.state.json",
        log_path=runtime_dir / f"{stem}.notebooklm.log",
    )


def emit_progress(message: str) -> None:
    print(f"[notebooklm-podcast] {message}", flush=True)


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


def find_notebooklm_py(auto_install: bool) -> str:
    candidates = [
        shutil.which("notebooklm"),
        str(Path.home() / ".local" / "bin" / "notebooklm"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate

    if not auto_install:
        raise SystemExit(
            "notebooklm-py CLI not found. Install notebooklm-py[cookies] or pass --install-notebooklm-py."
        )

    install = run([sys.executable, "-m", "pip", "install", "--user", "notebooklm-py[cookies]"])
    if install.returncode != 0:
        raise SystemExit(install.stderr or install.stdout)

    installed = Path.home() / ".local" / "bin" / "notebooklm"
    if not installed.exists():
        raise SystemExit("notebooklm-py install completed but ~/.local/bin/notebooklm was not found.")
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


def ensure_notebooklm_py_auth(notebooklm: str, env: dict[str, str]) -> None:
    probe = run_retry([notebooklm, "auth", "check", "--test"], env=env)
    if probe.returncode == 0:
        return

    emit_progress("notebooklm-py auth missing; reading cookies from Chrome")
    login = run([notebooklm, "login", "--browser-cookies", "chrome"], env=env)
    if login.returncode != 0:
        raise RuntimeError(login.stderr or login.stdout)

    verify = run_retry([notebooklm, "auth", "check", "--test"], env=env)
    if verify.returncode != 0:
        raise RuntimeError(verify.stderr or verify.stdout)


def first_uuid(text: str) -> str:
    match = UUID_RE.search(text)
    if not match:
        raise RuntimeError(f"could not parse notebook id from output:\n{text}")
    return match.group(0)


def create_notebook(nlm: str, env: dict[str, str], title: str) -> str:
    result = run_retry([nlm, "notebook", "create", title], env=env, check=True)
    return first_uuid(result.stdout + "\n" + result.stderr)


def add_source(nlm: str, env: dict[str, str], notebook_id: str, source: str, title: str) -> None:
    source_path = Path(source).expanduser()
    if source_path.exists():
        cmd = [nlm, "source", "add", "--name", title, notebook_id, str(source_path)]
        run_retry(cmd, env=env, check=True)
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


def create_audio(nlm: str, env: dict[str, str], notebook_id: str, instructions: str) -> None:
    result = run_retry([nlm, "create-audio", notebook_id, instructions], env=env)
    if result.returncode not in {0, 7}:
        raise RuntimeError(result.stderr or result.stdout)


def json_stdout(result: subprocess.CompletedProcess[str]) -> dict[str, object]:
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON output:\n{result.stdout}\n{result.stderr}") from exc


def create_notebook_with_notebooklm_py(notebooklm: str, env: dict[str, str], title: str) -> str:
    result = run_retry([notebooklm, "create", title, "--json"], env=env, check=True)
    payload = json_stdout(result)
    notebook = payload.get("notebook")
    if not isinstance(notebook, dict) or not isinstance(notebook.get("id"), str):
        raise RuntimeError(f"could not parse notebooklm-py notebook id from output:\n{result.stdout}")
    return notebook["id"]


def add_source_with_notebooklm_py(
    notebooklm: str, env: dict[str, str], notebook_id: str, source: str, title: str
) -> None:
    cmd = [notebooklm, "source", "add", source, "--notebook", notebook_id, "--title", title, "--json"]
    run_retry(cmd, env=env, check=True)


def create_audio_with_notebooklm_py(
    notebooklm: str, env: dict[str, str], notebook_id: str, instructions: str
) -> None:
    cmd = [
        notebooklm,
        "generate",
        "audio",
        instructions,
        "--notebook",
        notebook_id,
        "--format",
        "deep-dive",
        "--language",
        "zh_Hans",
        "--json",
    ]
    run_retry(cmd, env=env, check=True)


def latest_notebooklm_py_audio_status(payload: dict[str, object]) -> dict[str, object]:
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        raise RuntimeError(f"artifact list did not contain artifacts: {payload}")
    audio_artifacts = [
        artifact
        for artifact in artifacts
        if isinstance(artifact, dict) and artifact.get("type_id") == "audio"
    ]
    if not audio_artifacts:
        raise RuntimeError("no audio artifacts found yet")
    return audio_artifacts[-1]


def download_when_ready_with_notebooklm_py(
    notebooklm: str,
    env: dict[str, str],
    notebook_id: str,
    output: Path,
    timeout_seconds: int,
    poll_seconds: int,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    poll_count = 0
    last_error = ""
    while time.monotonic() < deadline:
        poll_count += 1
        emit_progress(f"poll {poll_count}: checking notebooklm-py audio artifact status")
        result = run_retry(
            [notebooklm, "artifact", "list", "--notebook", notebook_id, "--type", "audio", "--json"],
            env=env,
            attempts=2,
        )
        try:
            artifact = latest_notebooklm_py_audio_status(json_stdout(result))
        except Exception as exc:
            last_error = str(exc)
            emit_progress(f"poll {poll_count}: audio artifact not ready ({last_error}); retrying in {poll_seconds}s")
            time.sleep(poll_seconds)
            continue

        status = str(artifact.get("status", "unknown"))
        emit_progress(f"poll {poll_count}: audio artifact status={status}")
        if status.lower() not in {"completed", "complete", "ready"}:
            time.sleep(poll_seconds)
            continue

        download = run_retry(
            [
                notebooklm,
                "download",
                "audio",
                str(output),
                "--notebook",
                notebook_id,
                "--latest",
                "--force",
                "--json",
            ],
            env=env,
            attempts=2,
        )
        if download.returncode == 0 and output.exists() and output.stat().st_size > 0:
            emit_progress(f"poll {poll_count}: downloaded {output.name} ({output.stat().st_size} bytes)")
            return
        last_error = (download.stderr or download.stdout).strip()
        emit_progress(f"poll {poll_count}: download failed ({last_error}); retrying in {poll_seconds}s")
        time.sleep(poll_seconds)
    raise TimeoutError(f"audio download did not become ready. Last output: {last_error}")


def download_when_ready(
    nlm: str,
    env: dict[str, str],
    notebook_id: str,
    output: Path,
    timeout_seconds: int,
    poll_seconds: int,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error = ""
    poll_count = 0
    while time.monotonic() < deadline:
        poll_count += 1
        emit_progress(f"poll {poll_count}: checking audio download readiness")
        if output.exists():
            output.unlink()
        result = run_retry([nlm, "audio", "download", notebook_id, str(output)], env=env, attempts=2)
        if result.returncode == 0 and output.exists() and output.stat().st_size > 0:
            emit_progress(f"poll {poll_count}: downloaded {output.name} ({output.stat().st_size} bytes)")
            return
        last_error = (result.stderr or result.stdout).strip()
        concise_error = last_error.splitlines()[-1] if last_error else "audio not ready"
        emit_progress(f"poll {poll_count}: not ready ({concise_error}); retrying in {poll_seconds}s")
        time.sleep(poll_seconds)
    raise TimeoutError(f"audio download did not become ready. Last output: {last_error}")


def write_state(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def spawn_background(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = runtime_paths(output_dir, args.stem, Path(args.runtime_dir) if args.runtime_dir else None)
    paths.log_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [sys.executable, str(Path(__file__).resolve())]
    for key, value in vars(args).items():
        if key == "background" or value in {None, False}:
            continue
        flag = "--" + key.replace("_", "-")
        if value is True:
            cmd.append(flag)
        else:
            cmd.extend([flag, str(value)])

    with paths.log_path.open("ab") as log:
        proc = subprocess.Popen(
            cmd,
            stdout=log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )

    write_state(
        paths.state_path,
        {
            "status": "running",
            "pid": proc.pid,
            "log": str(paths.log_path),
            "output_dir": str(output_dir),
            "audio": str(paths.audio_path),
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        },
    )
    print(json.dumps({"pid": proc.pid, "log": str(paths.log_path), "state": str(paths.state_path)}, ensure_ascii=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a NotebookLM podcast package via nlm.")
    parser.add_argument("--source", required=True, help="Local file, URL, or literal text source.")
    parser.add_argument("--output-dir", required=True, help="Podcast package output directory.")
    parser.add_argument(
        "--runtime-dir",
        help="State/log directory. Defaults to a hidden sibling .media-writer-runtime folder outside output-dir.",
    )
    parser.add_argument("--title", required=True, help="Notebook and source title.")
    parser.add_argument("--stem", default="notebooklm_podcast", help="Output filename stem.")
    parser.add_argument(
        "--instructions",
        default="Generate a clear Chinese audio overview as a podcast-style deep dive.",
        help="NotebookLM audio instructions.",
    )
    parser.add_argument("--auth-profile", help="Browser profile name/path for nlm auth, e.g. Oje or 'Profile 9'.")
    parser.add_argument("--authuser", help="NLM_AUTHUSER value for multi-account profiles.")
    parser.add_argument(
        "--engine",
        choices=["notebooklm-py", "nlm"],
        default="notebooklm-py",
        help="Podcast CLI backend. notebooklm-py is preferred because it can download audio with Chrome cookies.",
    )
    parser.add_argument("--notebooklm", help="Path to notebooklm-py CLI binary.")
    parser.add_argument(
        "--install-notebooklm-py",
        action="store_true",
        help="Install notebooklm-py[cookies] with pip if missing.",
    )
    parser.add_argument("--nlm", help="Path to nlm binary.")
    parser.add_argument("--install-nlm", action="store_true", help="Install nlm with go install if missing.")
    parser.add_argument("--background", action="store_true", help="Detach and run in the background.")
    parser.add_argument("--timeout-minutes", type=int, default=45)
    parser.add_argument("--poll-seconds", type=int, default=30)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.background:
        spawn_background(args)
        return 0

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = runtime_paths(output_dir, args.stem, Path(args.runtime_dir) if args.runtime_dir else None)
    paths.state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path = paths.state_path
    audio_path = paths.audio_path

    payload: dict[str, object] = {
        "status": "starting",
        "output_dir": str(output_dir),
        "audio": str(audio_path),
        "state": str(state_path),
        "log": str(paths.log_path),
    }
    write_state(state_path, payload)

    try:
        env = env_with_authuser(args.authuser)
        if args.engine == "notebooklm-py":
            backend = args.notebooklm or find_notebooklm_py(args.install_notebooklm_py)
            emit_progress("checking notebooklm-py Chrome-cookie authentication")
            ensure_notebooklm_py_auth(backend, env)
            emit_progress(f"creating notebook: {args.title}")
            notebook_id = create_notebook_with_notebooklm_py(backend, env, args.title)
        else:
            backend = args.nlm or find_nlm(args.install_nlm)
            emit_progress("checking nlm CLI authentication")
            ensure_auth(backend, env, args.auth_profile)
            emit_progress(f"creating notebook: {args.title}")
            notebook_id = create_notebook(backend, env, args.title)
        payload.update({"status": "notebook_created", "notebook_id": notebook_id})
        write_state(state_path, payload)

        emit_progress("adding source to notebook")
        if args.engine == "notebooklm-py":
            add_source_with_notebooklm_py(backend, env, notebook_id, args.source, args.title)
        else:
            add_source(backend, env, notebook_id, args.source, args.title)
        payload["status"] = "source_added"
        write_state(state_path, payload)

        emit_progress("requesting NotebookLM audio generation")
        if args.engine == "notebooklm-py":
            create_audio_with_notebooklm_py(backend, env, notebook_id, args.instructions)
        else:
            create_audio(backend, env, notebook_id, args.instructions)
        payload["status"] = "audio_generating"
        payload["engine"] = args.engine
        write_state(state_path, payload)

        if args.engine == "notebooklm-py":
            download_when_ready_with_notebooklm_py(
                backend,
                env,
                notebook_id,
                audio_path,
                timeout_seconds=args.timeout_minutes * 60,
                poll_seconds=args.poll_seconds,
            )
        else:
            download_when_ready(
                backend,
                env,
                notebook_id,
                audio_path,
                timeout_seconds=args.timeout_minutes * 60,
                poll_seconds=args.poll_seconds,
            )
        payload.update(
            {
                "status": "complete",
                "audio": str(audio_path),
                "audio_size": audio_path.stat().st_size,
                "completed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
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
