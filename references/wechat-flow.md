# WeChat Draft Flow

Use this reference when converting a rewritten article into a WeChat Official Account draft.

## Inputs

- Source Markdown or fetched social post/article content.
- New article Markdown with frontmatter:

```yaml
---
title: "AI 视频生产线来了"
author: "Codex"
digest: "Codex + HyperFrames 正在把视频生产从剪辑软件里搬出来，变成一条可描述、可生成、可迭代的 AI 工作流。"
source: "https://x.com/example/status/..."
---
```

## Required Configuration

Draft upload requires a configured local `md2wechat` workspace. The user must keep secrets outside this skill repository.

Required for real WeChat draft upload:

- WeChat Official Account `APPID`
- WeChat Official Account `SECRET`
- Current machine/server IP added to the WeChat Official Account IP whitelist
- Working `md2wechat` CLI

Optional, depending on workflow:

- `md2wechat` API key for API-mode conversion
- Image provider key for cover/image generation

Do not commit `md2wechat.yaml`, `.env`, or other secret-bearing files.

## Discovery

Run from the md2wechat project directory, not from the arbitrary workspace:

```powershell
cd "C:\Users\Administrator\Documents\Codex\2026-04-22-md2wechat-1-curl-fssl-https-github"
.\tools\md2wechat\md2wechat.exe version --json
.\tools\md2wechat\md2wechat.exe capabilities --json
.\tools\md2wechat\md2wechat.exe config show --format json
.\tools\md2wechat\md2wechat.exe config validate
```

Treat live help as the authority:

```bash
md2wechat --help
```

There are two command surfaces in the wild:

1. Subcommand mode: supports `version`, `capabilities`, `upload_image`, and `create_draft`.
2. Direct-publish mode: supports flags such as `--markdown`, `--html`, `--cover`, `--title`, and `--summary`, and creates the draft in one command.

If `version --json` fails as an unknown argument and `--help` shows direct publish flags, use direct-publish mode. Python package installs of direct-publish mode read WeChat credentials from `.env` or `WECHAT_APPID` / `WECHAT_APP_SECRET`; they may ignore `md2wechat.yaml`.

## Convert Markdown To Local HTML

```powershell
$env:MD2WECHAT_OUTPUT_DIR="C:\path\to\output"
& "C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
  "C:\path\to\skill\scripts\publish_markdown_to_wechat.py" `
  "C:\path\to\article.md" `
  "C:\Users\Administrator\Documents\Codex\2026-04-22-md2wechat-1-curl-fssl-https-github\tools\md2wechat\md2wechat.exe"
```

Outputs:

- `<stem>.wechat.html`
- `<stem>.image-map.json`
- `<stem>_cover.jpg` when the article contains a first local image

## Cover

Draft upload requires a cover media id.

If configured image generation works:

```powershell
.\tools\md2wechat\md2wechat.exe generate_cover --article "C:\path\to\article.md" --preset cover-hero --aspect 16:9 --size 2560x1440 --json
```

If image generation fails, create a local JPG cover with the bundled fallback:

```powershell
.\scripts\New-LocalWechatCover.ps1 `
  -Output "C:\path\to\cover.jpg" `
  -Title "Article title" `
  -Subtitle "Short cover subtitle" `
  -Kicker "市场观察" `
  -Theme market
```

Upload cover:

```powershell
.\tools\md2wechat\md2wechat.exe upload_image "C:\path\to\cover.jpg" --json
```

Save `data.media_id`.

## Build Draft JSON

```powershell
& "C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
  "C:\path\to\skill\scripts\make_wechat_draft_json.py" `
  --markdown "C:\path\to\article.md" `
  --html "C:\path\to\article.wechat.html" `
  --thumb-media-id "<cover_media_id>" `
  --output "C:\path\to\article.draft.json"
```

## Upload Draft

```powershell
.\tools\md2wechat\md2wechat.exe create_draft "C:\path\to\article.draft.json" --json
```

Success returns a draft `media_id`.

## Direct-Publish Fallback

When the installed CLI exposes direct flags instead of `upload_image` and `create_draft`, convert local HTML first, create a local cover JPG, then call:

```bash
md2wechat \
  --html "{article.wechat.html}" \
  --title "{title}" \
  --summary "{digest}" \
  --author "{author}" \
  --cover "{cover.jpg}" \
  --style tech
```

The direct-publish CLI uploads the cover and returns the draft `media_id` in its JSON result. If it returns `40125 invalid appsecret`, compare the live `.env` or environment variables with the intended Official Account credentials before retrying.

## Notes

- If `convert --draft` fails because of md2wechat API credentials, use the local HTML plus `create_draft` flow.
- If WeChat returns `40164 invalid ip`, add the reported IP to the Official Account IP whitelist and retry.
- If WeChat returns `41039 invalid content_source_url`, make sure `content_source_url` is empty or a real `http/https` URL. Local file paths are rejected by WeChat.
- Do not use `npx md2wechat` when a local configured executable is available.
