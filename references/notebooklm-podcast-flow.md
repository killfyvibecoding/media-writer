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

## Audio Generation Sequence

For Get笔记 transcript extraction, token lookup order is `GETNOTE_TOKENS_FILE`, `~/.codex/skills/getnote/tokens.json`, then `~/.claude/skills/getnote/tokens.json`.

Adapt commands to the installed NotebookLM CLI. Treat live `--help` output as the authority.

```powershell
notebooklm create "{notebook_title}"
notebooklm source add "{source_path_or_url}" --title "{source_title}"
notebooklm generate audio --instructions "{optional_user_style_or_duration_request}"
notebooklm artifact wait "{task_id}"
notebooklm download audio "{output_mp3}"
```

If the CLI returns notebook/source/artifact IDs, store them in a small resumable note or script so retries can continue instead of starting over.

## Required Podcast Artifacts

Create title/description TXT:

```powershell
& "{python}" "{skill_dir}\scripts\make_podcast_info.py" `
  --title "{podcast_title}" `
  --description "{podcast_description}" `
  --output "{output_dir}\{stem}_podcast_info.txt"
```

Create fallback cover when md2wechat image generation is unavailable:

```powershell
& "{python}" "{skill_dir}\scripts\make_podcast_cover.py" `
  --title "{podcast_title}" `
  --subtitle "{one_sentence_hook}" `
  --output "{output_dir}\{stem}_podcast_cover.jpg"
```

Build the WeChat wrapper Markdown:

```powershell
& "{python}" "{skill_dir}\scripts\build_podcast_wechat_markdown.py" `
  --audio "{output_dir}\{stem}.mp3" `
  --info "{output_dir}\{stem}_podcast_info.txt" `
  --cover "{output_dir}\{stem}_podcast_cover.jpg" `
  --source-title "{source_title}" `
  --source-url "{source_url}" `
  --output "{output_dir}\{stem}_wechat_podcast.md"
```

If the user also asked for WeChat draft upload, switch to [wechat-flow.md](wechat-flow.md) and use the unchanged `media-transfer` upload sequence after completing the podcast package.

## WeChat Audio Reality Check

The inherited `media-transfer` workflow creates a WeChat Official Account article draft. It reliably handles Markdown/HTML, body images, cover upload, draft JSON, and draft creation.

It does not, by itself, prove MP3 embedding is supported. Before saying the WeChat draft contains embedded audio:

1. Run `md2wechat capabilities --json` from the configured md2wechat workspace.
2. Look for explicit audio/voice material upload and draft insertion support.
3. If support exists, use that documented command and record the returned media ID.
4. If support does not exist, keep the MP3 as a generated local artifact and reference it in the draft body/final report.
