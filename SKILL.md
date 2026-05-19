---
name: media-writer
description: "Use when the user wants either or both of these workflows: generate a NotebookLM podcast/audio package from any readable source, or transform readable source content into a rewritten WeChat Official Account draft using media-transfer logic. Triggers include 生成播客, 做成音频, 标题简介, 播客封面, 上传微信公众号草稿, 生成微信草稿, or combined podcast plus WeChat draft requests."
---

# Media Writer

Route requests across two independent layers: NotebookLM podcast generation and WeChat draft publishing. Run either layer alone, or run both when the user explicitly asks for both.

This skill merges two responsibilities without forcing them into a single automatic chain:

1. **Podcast layer** from `qiaomu-anything-to-notebooklm`: collect source content, upload/create a NotebookLM source, generate audio, then produce MP3 + title/description TXT + podcast cover JPG.
2. **WeChat draft layer** from `media-transfer`: read the source, analyze it, rewrite a new platform-ready article, convert Markdown to WeChat HTML, upload cover, build draft JSON, and create the draft through the configured `md2wechat` CLI.

## Hard Boundaries

- Do not treat "生成播客" as an automatic request to upload a WeChat draft.
- Do not treat "上传微信公众号草稿" as an automatic request to generate a podcast.
- Run both layers only when the user asks for both, such as "生成播客，带标题简介和封面，并上传到公众号草稿".
- Do not rewrite or bypass the copied `media-transfer` publishing scripts unless the user explicitly asks to change that logic.
- In the podcast layer, do not skip MP3, title/description TXT, or podcast cover JPG.
- In the WeChat draft layer, do not skip the media-transfer analysis and rewrite step unless the user explicitly asks for direct conversion only.
- Do not claim the MP3 is embedded inside the WeChat draft unless the live `md2wechat capabilities --json` output or WeChat workflow explicitly supports audio/voice insertion.

## Intent Routing

Use the user's wording to choose one or both layers:

| User intent | Run |
| --- | --- |
| "生成播客", "做成音频", "转成播客", "给我音频、标题简介、封面" | Podcast layer only |
| "上传到微信公众号草稿", "生成微信草稿", "改写成公众号并上传草稿" | WeChat draft layer only |
| "生成播客，并上传到微信公众号草稿", "音频标题简介封面，再发公众号草稿" | Podcast layer + WeChat draft layer |
| "直接转换/直接上传，不改写" | WeChat draft layer without analysis/rewrite only if explicitly requested |

## Podcast Layer

When the user asks for podcast/audio:

1. **Identify and collect source**
   - Use the source rules in [references/notebooklm-podcast-flow.md](references/notebooklm-podcast-flow.md).
   - For YouTube, pass the URL directly to NotebookLM; do not download subtitles.
   - For X/Twitter or paywalled pages, use `scripts/fetch_url.sh` only when direct NotebookLM URL ingestion is insufficient.
   - For xiaoyuzhou/ximalaya/bilibili-style audio/video links, use `scripts/get_podcast_transcript.py` when transcript extraction is needed.

2. **Generate NotebookLM audio**
   - Create or reuse the requested NotebookLM notebook.
   - Add the source, run audio generation, wait for completion, and download the MP3.
   - Preserve generated IDs or use a resumable script when the operation may take a long time.

3. **Generate podcast metadata**
   - Create `<stem>_podcast_info.txt` with `scripts/make_podcast_info.py`.
   - The TXT must contain exactly two sections: `标题：` and `简介：`.
   - Title target: clear Chinese title, ideally 18-30 Chinese characters.
   - Description target: 120-220 Chinese characters; include risk/disclaimer text for finance or market topics.

4. **Generate podcast cover**
   - Prefer `md2wechat generate_cover --article ... --preset cover-hero --aspect 16:9 --size 2560x1440 --json` when configured.
   - If remote image generation fails, use `scripts/make_podcast_cover.py`.
   - If a WeChat-specific fallback cover is needed, use `scripts/New-LocalWechatCover.ps1`.

5. **Report podcast package**
   - Return MP3 path, title/description TXT path, and cover JPG path.
   - If the user also asked for WeChat upload, continue to the WeChat draft layer.

## WeChat Draft Layer

When the user asks to upload/create a WeChat Official Account draft, use the original `media-transfer` logic:

1. **Read or fetch the source**
   - Accept pasted text, local Markdown, Obsidian clippings, X/Twitter URLs, public web URLs, blog/newsletter links, and readable long-form documents.
   - Prefer a user-provided Markdown file when available.
   - If the user provides a URL, fetch readable article/post content with available web, browser, or source-specific tooling.
   - If PowerShell displays mojibake, reread files with explicit UTF-8 or use Python scripts that read UTF-8.

2. **Analyze and tear down the source**
   - Identify the original title strategy, opening hook, target reader, promise, narrative structure, examples, data points, CTA, and gaps.
   - Separate reusable ideas from wording that must not be copied.
   - Note what should be preserved as insight, what should be reframed, and what should be removed or strengthened.
   - If the user asks to see the analysis first, present the teardown before writing.

3. **Rewrite a new WeChat-ready article**
   - Write a new article rather than copying or lightly paraphrasing the source.
   - Change the angle, structure, voice, examples, transitions, and title while preserving the useful core insight.
   - For Chinese WeChat articles, prefer concrete scenes, clear paragraphs, useful frameworks, and a stronger opening hook.
   - Include Markdown frontmatter: `title`, `author`, `digest`, and `source`.
   - Keep WeChat metadata safe: `title` <= 32 Chinese characters, `author` <= 16 characters, `digest` <= 128 characters.

4. **Prepare WeChat artifacts**
   - Read [references/wechat-flow.md](references/wechat-flow.md) for exact commands.
   - Run md2wechat discovery from the configured md2wechat workspace before first upload in a session.
   - Run `scripts/publish_markdown_to_wechat.py` to create `.wechat.html`, `.image-map.json`, and image upload mappings.
   - Prepare a cover. Prefer `md2wechat generate_cover`; if unavailable, use `scripts/New-LocalWechatCover.ps1` or ask for a cover.

5. **Create/upload the draft**
   - Upload the cover with `md2wechat upload_image`.
   - Build draft JSON with `scripts/make_wechat_draft_json.py`.
   - Upload with `md2wechat create_draft <draft.json> --json`.
   - Report the returned WeChat draft `media_id`.

## Combined Request Flow

When the user asks for podcast generation and WeChat draft upload in the same request:

1. Run the podcast layer and produce MP3 + title/description TXT + podcast cover JPG.
2. Run the WeChat draft layer from the same source using `media-transfer` analysis and rewrite logic.
3. If useful, use the podcast title/description/cover as inputs or references for the WeChat article, but do not replace the media-transfer article analysis and rewrite.
4. Upload the rewritten WeChat article draft using the unchanged `media-transfer` upload flow.
5. Report both result groups: podcast package paths and WeChat draft `media_id`.

## Output Checklist

For podcast-layer output, report:

- NotebookLM source/notebook used, when available.
- MP3 path.
- Title/description TXT path.
- Cover JPG path.

For WeChat-draft-layer output, report:

- Source read/fetch status.
- Analysis/rewrite status.
- Rewritten Markdown path, when saved.
- WeChat HTML path and draft JSON path.
- WeChat draft `media_id`.
- Whether the audio was embedded or only referenced, based on live capability evidence.

## Local Resource Map

NotebookLM/source utilities copied from `qiaomu-anything-to-notebooklm`:

- `scripts/fetch_url.sh`
- `scripts/get_podcast_transcript.py`
- `scripts/make_podcast_cover.py`
- `scripts/make_podcast_info.py`

Optional podcast-to-WeChat wrapper helper, only for requests that explicitly need a Markdown wrapper around generated podcast assets:

- `scripts/build_podcast_wechat_markdown.py`

Publishing utilities copied from `media-transfer`:

- `scripts/publish_markdown_to_wechat.py`
- `scripts/make_wechat_draft_json.py`
- `scripts/New-LocalWechatCover.ps1`

Detailed references:

- [references/notebooklm-podcast-flow.md](references/notebooklm-podcast-flow.md)
- [references/wechat-flow.md](references/wechat-flow.md)

## Common Failure Modes

- NotebookLM login missing: run `notebooklm login`, then verify with `notebooklm list` or the installed CLI equivalent.
- PowerShell displays mojibake: prefer UTF-8 file reads and Python scripts; verify bytes or output files when display encoding looks wrong.
- `md2wechat` image generation credentials fail: use `scripts/make_podcast_cover.py` or `scripts/New-LocalWechatCover.ps1`.
- WeChat `40164 invalid ip`: ask the user to add the reported IP to the Official Account IP whitelist, then retry.
- WeChat `41039 invalid content_source_url`: keep `content_source_url` empty or use a real `https://...` URL; never pass local file paths as source URLs.
- Audio cannot be embedded: do not invent a public audio URL. Report the MP3 path and explicitly state the audio is referenced rather than embedded.
