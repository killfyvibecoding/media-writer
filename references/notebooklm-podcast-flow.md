# NotebookLM Podcast Flow

Use this reference when collecting sources and generating podcast/audio artifacts. Continue to the unchanged `media-transfer` WeChat draft flow only when the user also asks to create or upload a WeChat Official Account draft.

## Source Routing

| Input | Route |
| --- | --- |
| `https://mp.weixin.qq.com/s/...` | Fetch readable article content when MCP/tooling is available, save as TXT/Markdown, then add to NotebookLM. |
| YouTube URL | Add the URL directly to NotebookLM. Do not use yt-dlp, browser automation, Whisper, or subtitle download. |
| `xiaoyuzhoufm.com`, `ximalaya.com`, `bilibili.com` | Use `scripts/get_podcast_transcript.py <URL>` when a transcript is needed, then add the transcript file to NotebookLM. |
| `x.com` or `twitter.com` | Use direct source handling first; if blocked, use `scripts/fetch_url.sh "<URL>"` and add the resulting Markdown/TXT. |
| Normal public web URL | Prefer direct NotebookLM URL ingestion. |
| Paywalled or blocked web URL | Use `scripts/fetch_url.sh "<URL>"` only when direct ingestion fails or would be incomplete. |
| Local `.md`/`.txt` | Add directly as a source. |
| PDF/DOCX/PPTX/XLSX/EPUB/image/audio/ZIP | Convert or transcribe to TXT/Markdown using available local conversion tools, then add the converted file. |
| Search query | Search, summarize 3-5 sources into a TXT/Markdown source, then add it to NotebookLM. |

## CLI-First Audio Generation Sequence

Use the same terminal CLI workflow on macOS, Windows, and Linux. Do not branch into browser control just because the host is macOS. Browser interaction is only for one-time Google login or as a last-resort fallback when the CLI cannot operate.

Preferred podcast CLI:

```bash
python -m pip install --user "notebooklm-py[cookies]"
notebooklm login --browser-cookies chrome
notebooklm auth check --test
```

The default podcast script backend is `notebooklm-py`, not `tmc/nlm`. `notebooklm-py` can read the already logged-in Chrome cookies and download generated audio from the terminal. Current `tmc/nlm` builds can generate audio but may fail at audio download with `Google CDN requires browser session cookies`, so use it only through `--engine nlm` as a compatibility fallback.

On Windows, the same principle applies: use the terminal CLI with an authenticated browser-cookie store. The reason a previous Windows run may have worked without visible browser control was an environment difference: the required authenticated CLI/browser-cookie state was already available.

Preferred script entrypoint when the user expects the finished audio in the same run:

```bash
python "{skill_dir}/scripts/run_notebooklm_podcast.py" \
  --source "{source_path_or_url}" \
  --output-dir "{output_dir}" \
  --title "{notebook_title}" \
  --stem "{stem}" \
  --instructions "{diagnosis_driven_podcast_instructions}" \
  --install-notebooklm-py
```

When a readable source exists, create `{stem}_content_diagnosis.md` and `{stem}_content_diagnosis.json` first with [content-diagnosis-flow.md](content-diagnosis-flow.md). Build `--instructions` from `podcast_strategy` in the diagnosis JSON:

- listener profile
- opening hook
- main angle
- must-cover points
- skip/weak points
- tone
- risk notes

The foreground script keeps printing terminal poll progress until the audio is ready or the timeout is reached. Use `--background` only for a detached job the user does not expect to watch to completion.

The script writes user-facing deliverables to `{output_dir}`:

- `{stem}.m4a` when audio is ready through the default backend

By default it writes runtime evidence outside the delivery folder:

- `{output_dir_parent}/.media-writer-runtime/{output_dir_name}/{stem}.notebooklm.state.json`
- `{output_dir_parent}/.media-writer-runtime/{output_dir_name}/{stem}.notebooklm.log` when run with `--background`

Use `--runtime-dir` only when a job needs a specific state/log location. Use the state JSON and log for progress checks. Do not open NotebookLM in a browser unless the state/log shows a real CLI blocker.

## Raw nlm Commands

For Get笔记 transcript extraction, token lookup order is `GETNOTE_TOKENS_FILE`, `~/.codex/skills/getnote/tokens.json`, then `~/.claude/skills/getnote/tokens.json`.

Adapt commands to the installed `nlm` CLI. Treat live `--help` output as the authority.

```bash
notebook_id="$(nlm notebook create "{notebook_title}" | sed -nE 's/.*([0-9a-f-]{36}).*/\1/p' | head -1)"
nlm source add --name "{source_title}" "$notebook_id" "{source_path_or_url}"
nlm create-audio "$notebook_id" "{optional_user_style_or_duration_request}"
nlm audio download "$notebook_id" "{output_mp3}"
```

If the CLI returns notebook/source/artifact IDs, store them in a state JSON so retries can continue instead of starting over. Prefer `scripts/run_notebooklm_podcast.py` because it already does this.

Artifact and study-output flows may still use `tmc/nlm` where its command surface is the best fit:

```bash
go install github.com/tmc/nlm/cmd/nlm@latest
nlm auth "<Chrome profile name>"
nlm notebook list
```

## Required Podcast Artifacts

The CLI script only creates the NotebookLM audio file. Still create the metadata TXT and cover JPG with the bundled scripts.

Create title/description TXT:

```powershell
& "{python}" "{skill_dir}\scripts\make_podcast_info.py" `
  --title "{diagnosis_podcast_title}" `
  --description "{diagnosis_podcast_description}" `
  --output "{output_dir}\{stem}_podcast_info.txt"
```

Create fallback cover when md2wechat image generation is unavailable:

```powershell
& "{python}" "{skill_dir}\scripts\make_podcast_cover.py" `
  --title "{diagnosis_podcast_title}" `
  --subtitle "{diagnosis_podcast_hook}" `
  --output "{output_dir}\{stem}_podcast_cover.jpg"
```

Build the WeChat wrapper Markdown:

```powershell
& "{python}" "{skill_dir}\scripts\build_podcast_wechat_markdown.py" `
  --audio "{output_dir}\{stem}.m4a" `
  --info "{output_dir}\{stem}_podcast_info.txt" `
  --cover "{output_dir}\{stem}_podcast_cover.jpg" `
  --source-title "{source_title}" `
  --source-url "{source_url}" `
  --output "{output_dir}\{stem}_wechat_podcast.md"
```

If the user also asked for WeChat draft upload, switch to [wechat-flow.md](wechat-flow.md) and use the unchanged `media-transfer` upload sequence after completing the podcast package.

## WeChat Audio Reality Check

The inherited `media-transfer` workflow creates a WeChat Official Account article draft. It reliably handles Markdown/HTML, body images, cover upload, draft JSON, and draft creation.

It does not, by itself, prove audio embedding is supported. Before saying the WeChat draft contains embedded audio:

1. Run `md2wechat capabilities --json` from the configured md2wechat workspace.
2. Look for explicit audio/voice material upload and draft insertion support.
3. If support exists, use that documented command and record the returned media ID.
4. If support does not exist, keep the audio file as a generated local artifact and reference it in the draft body/final report.
