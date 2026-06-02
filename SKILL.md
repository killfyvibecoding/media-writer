---
name: media-writer
description: "Use when the user wants content diagnosis/value analysis before NotebookLM output, a PPT+podcast HyperFrames MP4 video, a rewritten WeChat draft, or a Xiaohongshu 科普帖. NotebookLM outputs include 播客/音频, PPT/幻灯片, 思维导图/脑图, Quiz/测验, 视频, 报告, 信息图, 数据表, 闪卡, summary/outline/FAQ/study guide. WeChat triggers include 上传微信公众号草稿/生成微信草稿. Xiaohongshu triggers include 小红书文稿/小红书帖子/小红书标签."
---

# Media Writer

Route requests through a content diagnosis preflight, then across four independent output layers: NotebookLM artifact generation, PPT+podcast video composition, WeChat draft publishing, and Xiaohongshu 科普帖 packaging. Run any output layer alone, or run multiple layers when the user asks for them in the same output pool.

This skill merges one diagnosis preflight plus four output responsibilities without forcing them into a single automatic chain:

0. **Content diagnosis layer** inspired by `dbskill`: diagnose content value, propagation value, five quality dimensions, platform fit, keep/drop/risk points, and podcast strategy before generation.
1. **NotebookLM layer** from `qiaomu-anything-to-notebooklm`: collect source content, run NotebookLM through terminal CLIs, then generate the requested output: podcast/audio, PPT/slide deck, mind map, video, report, quiz, flashcards, infographic brief, data table, or text study artifacts.
2. **PPT+podcast video layer**: consume generated or provided slides plus podcast audio, build a HyperFrames project, add strong narrative motion/captions/keyword overlays, and render a final 16:9 MP4.
3. **WeChat draft layer** from `media-transfer`: read the source, analyze it, rewrite a new platform-ready article, convert Markdown to WeChat HTML, upload cover, build draft JSON, and create the draft through the configured `md2wechat` CLI.
4. **Xiaohongshu layer**: read and analyze the same source, then produce a copy-ready Xiaohongshu 科普帖 package with title candidates, explainer-style body, related hot-style hashtags, and cover suggestion.

## Hard Boundaries

- Do not treat "生成播客" as an automatic request to upload a WeChat draft.
- Do not treat "生成播客" or "做PPT" as an automatic request to generate Xiaohongshu content unless the user asked for 小红书 output or configured the current task as a combined output pool.
- Do not treat "做成PPT", "生成幻灯片", "思维导图", or "脑图" as a podcast request.
- Do not treat "上传微信公众号草稿" as an automatic request to generate a podcast.
- Run multiple layers only when the user asks for them, such as "生成播客、PPT、脑图、微信草稿和小红书帖子".
- When a readable source is available, run the Content Diagnosis Layer before generating podcast, WeChat, Xiaohongshu, PPT, mind map, report, or video outputs. Exceptions: direct conversion requested by the user, or tasks that only combine already finished assets.
- Do not treat diagnosis as a user-facing replacement for the requested output. It is a pre-generation control file that must shape the output.
- For podcast/audio requests, do not use generic NotebookLM instructions when a diagnosis exists. Use the diagnosis `podcast_strategy` for angle, listener, hook, tone, must-cover points, skip points, title, description, and cover direction.
- Do not rewrite or bypass the copied `media-transfer` publishing scripts unless the user explicitly asks to change that logic.
- In the podcast layer, do not skip downloadable audio, title/description TXT, or podcast cover JPG. The default podcast backend currently delivers NotebookLM audio as `.m4a`; do not rename it to `.mp3` unless a real transcode created an MP3.
- Keep podcast delivery folders clean: final folders should contain only user-facing deliverables such as audio, title/description TXT, and cover JPG. Keep NotebookLM state/log/runtime files outside the delivery folder.
- For PPT and mind map requests, use the NotebookLM artifact script and preserve notebook/source/artifact IDs in state JSON.
- A Markdown slide draft is not a completed PPT request. Deliver an actual visual deck file such as `.pptx` or a native NotebookLM slide export; Markdown may only be an intermediate source.
- A Markdown mind-map draft is not a completed mind-map request when the user expects a viewable map. Deliver a visual mind-map file such as `.png`/`.svg`, or a native NotebookLM interactive map export/link verified by UI evidence.
- For `PPT + 播客 + 视频` requests, do not route to NotebookLM native `video`. Generate or resolve PPT/slides and podcast audio first, then run the HyperFrames PPT+podcast video layer.
- Do not create a silent ffmpeg-only fallback for PPT+podcast video. If HyperFrames fails, run diagnostics, write the manifest, and report the failure.
- Do not claim a PPT+podcast video is complete unless `{stem}_video.mp4` exists and is non-empty.
- In the WeChat draft layer, do not skip the media-transfer analysis and rewrite step unless the user explicitly asks for direct conversion only.
- Do not claim the audio is embedded inside the WeChat draft unless the live `md2wechat capabilities --json` output or WeChat workflow explicitly supports audio/voice insertion.
- Do not upload or publish to Xiaohongshu unless a separate Xiaohongshu publishing tool exists and the user explicitly asks for upload. Default Xiaohongshu output is local Markdown/JSON for manual copy-paste.
- Do not use browser UI automation for NotebookLM unless the terminal CLI path fails after authentication/install attempts. Windows and macOS should use the same CLI-first workflow.

## Intent Routing

Use the user's wording to choose one or more layers:

| User intent | Run |
| --- | --- |
| "生成播客", "做成音频", "转成播客", "给我音频、标题简介、封面" | Podcast layer only |
| "做成PPT", "生成幻灯片", "做个演示", "整理成演示" | NotebookLM `slides` artifact |
| "画个思维导图", "生成脑图", "做个导图", "梳理结构图" | NotebookLM `mindmap` artifact |
| "PPT和播客合成视频", "把PPT配播客做成视频", "生成PPT、播客、视频", "用现有PPT和播客生成视频" | PPT+podcast HyperFrames video layer; generate/resolve PPT and podcast first when needed |
| "生成Quiz", "出题", "做个测验" | NotebookLM `quiz` Markdown artifact |
| "做个视频", "生成视频" with no PPT/podcast/audio synthesis context | NotebookLM `video` artifact |
| "生成报告", "写个总结", "整理成文档" | NotebookLM `report` or text artifact |
| "做个信息图", "可视化" | NotebookLM `infographic` Markdown brief |
| "生成数据表", "做个表格" | NotebookLM `data-table` Markdown artifact |
| "做成闪卡", "生成记忆卡片" | NotebookLM `flashcards` Markdown artifact |
| "上传到微信公众号草稿", "生成微信草稿", "改写成公众号并上传草稿" | WeChat draft layer only |
| "小红书文稿", "小红书帖子", "小红书笔记", "小红书标签", "生成小红书" | Xiaohongshu layer only |
| "生成播客，并上传到微信公众号草稿", "PPT/脑图/音频，再发公众号草稿", "同步生成小红书" | Requested NotebookLM layer(s) + WeChat and/or Xiaohongshu layer(s) |
| "直接转换/直接上传，不改写" | WeChat draft layer without analysis/rewrite only if explicitly requested |

## Content Diagnosis Layer

Run this layer before any generation branch when a readable source is available.

1. **Read and diagnose the source**
   - Use [references/content-diagnosis-flow.md](references/content-diagnosis-flow.md).
   - Diagnose content value and propagation value separately.
   - Apply the five dimensions: 文字洁癖, 标题/封面/开头, 表达效率, 认知落差, 平台适配/AI辅助.
   - Identify concept traps, false assumptions, unsupported claims, useful material, keep/drop/risk points, and platform-specific strategy.
   - For weak but readable sources, do not block generation. Record the weakness, choose the best salvage angle, and continue.

2. **Create diagnosis package**
   - Use `scripts/make_content_diagnosis.py` to create `{stem}_content_diagnosis.md` and `{stem}_content_diagnosis.json`.
   - The JSON is the cross-branch source of truth for podcast, WeChat, Xiaohongshu, PPT, and mind-map generation.
   - Keep the diagnosis files in the same final output folder as the requested deliverables unless the task explicitly requires a separate runtime directory.

3. **Route branch prompts through the diagnosis**
   - Podcast: consume `podcast_strategy` for NotebookLM `--instructions`, title/description TXT, and cover direction.
   - WeChat: consume `core_insight`, `cognitive_gap`, `rewrite_angle`, and keep/drop/risk points before rewriting.
   - Xiaohongshu: consume the strongest cognitive gap and platform strategy to create a 科普帖, not a compressed long article.
   - PPT: consume the core insight and narrative angle before writing `{stem}_ppt_design_prompts.md`.
   - Mind map: use the diagnosis hierarchy instead of a flat source outline.

## NotebookLM Artifact Layer

When the user asks for PPT, mind map, video, report, quiz, flashcards, infographic, data table, summary, outline, FAQ, study guide, briefing doc, timeline, or table of contents:

1. **Identify and collect source**
   - Use [references/notebooklm-artifact-flow.md](references/notebooklm-artifact-flow.md).
   - For YouTube, pass the URL directly to NotebookLM; do not download subtitles.
   - For multiple URLs/files, pass each as a repeated `--source` argument.
   - For local PPTX/PDF/DOCX/Markdown, add the file directly when `nlm source add` supports it; otherwise convert to Markdown/TXT first.
   - If the source is readable, run the Content Diagnosis Layer first and keep the diagnosis Markdown/JSON with the artifact outputs.

2. **Generate the requested artifact**
   - Use `scripts/run_notebooklm_artifact.py` as the default entrypoint.
   - Run it with `--background` for long jobs.
   - Use `--kind slides` for PPT/幻灯片 and `--kind mindmap` for 思维导图/脑图.
   - For PPT/slide requests, first read [references/ppt-design-module.md](references/ppt-design-module.md), generate `{stem}_ppt_design_prompts.md` from the diagnosis `core_insight`, `rewrite_angle`, and narrative strategy, then use that design file as the visual source of truth for native NotebookLM instructions or rendered `.pptx` fallback.
   - For mind-map requests, use the diagnosis to decide the hierarchy: core insight, supporting logic, examples, risks, then actions/platform implications.
   - Use live `nlm --help` output as the authority. If a native artifact command fails on a valid notebook/source, generate a conservative Markdown intermediate through `generate-chat`, report the method plus native error, then render the final visual deliverable.

3. **Report the artifact package**
   - Return state JSON path, log path if backgrounded, notebook ID, source IDs, and artifact/output file path.
   - For slides, report the PPT design prompt file and the NotebookLM artifact details/export when native generation succeeds; otherwise render a real `.pptx` with the presentations workflow from the Markdown intermediate and the design prompt file, then report that visual file. Do not claim local PPTX/PDF download unless a command created one.
   - For mind maps, report the native NotebookLM map when it is genuinely available; otherwise render a viewable `.png`/`.svg` from the Markdown intermediate and report that visual file plus fallback method.

## Podcast Layer

When the user asks for podcast/audio:

1. **Identify and collect source**
   - Use the source rules in [references/notebooklm-podcast-flow.md](references/notebooklm-podcast-flow.md).
   - For YouTube, pass the URL directly to NotebookLM; do not download subtitles.
   - For X/Twitter or paywalled pages, use `scripts/fetch_url.sh` only when direct NotebookLM URL ingestion is insufficient.
   - For xiaoyuzhou/ximalaya/bilibili-style audio/video links, use `scripts/get_podcast_transcript.py` when transcript extraction is needed.
   - If the source is readable, run the Content Diagnosis Layer first.

2. **Generate NotebookLM audio**
   - Read [references/notebooklm-podcast-flow.md](references/notebooklm-podcast-flow.md).
   - Use `scripts/run_notebooklm_podcast.py` as the default entrypoint. Its default podcast backend is `notebooklm-py`, because it can authenticate from Chrome cookies and download the generated audio from the terminal. Keep `--engine nlm` only as a compatibility fallback when its installed version can complete the request.
   - When the user is waiting for a completed podcast delivery, run it in the terminal foreground so the poll loop keeps printing progress until the audio is ready. Use `--background` only when the user explicitly wants a detached job or a later status check.
   - Build `--instructions` from diagnosis `podcast_strategy`: listener profile, opening hook, core angle, must-cover points, skip points, tone, and risk notes. Do not send generic "deep dive" instructions when the diagnosis exists.
   - It creates a NotebookLM notebook, adds the source, starts audio generation, polls until ready, and downloads the audio file.
   - If authentication is missing, run `nlm auth <profile>` or let the script invoke auth. The user may need to complete a Google login page once.
   - Preserve the generated `.notebooklm.state.json` and `.notebooklm.log` files outside the delivery folder so retries can continue with evidence instead of guessing.

3. **Generate podcast metadata**
   - Create `<stem>_podcast_info.txt` with `scripts/make_podcast_info.py`.
   - The TXT must contain exactly two sections: `标题：` and `简介：`.
   - Prefer the diagnosis `podcast_strategy.title` and `podcast_strategy.description`; refine only to satisfy length and safety constraints.
   - Title target: clear Chinese title, ideally 18-30 Chinese characters.
   - Description target: 120-220 Chinese characters; include diagnosis risk notes for finance, market, medical, legal, or policy topics.

4. **Generate podcast cover**
   - Prefer `md2wechat generate_cover --article ... --preset cover-hero --aspect 16:9 --size 2560x1440 --json` when configured.
   - If remote image generation fails, use `scripts/make_podcast_cover.py`.
   - Use the diagnosis `podcast_strategy.cover_direction` as the visual direction.
   - If a WeChat-specific fallback cover is needed, use `scripts/New-LocalWechatCover.ps1`.

5. **Report podcast package**
   - Return audio path, title/description TXT path, and cover JPG path.
   - If the user also asked for WeChat upload, continue to the WeChat draft layer.

## PPT+Podcast Video Layer

When the user asks to combine PPT/slides and podcast/audio into a video, use [references/ppt-podcast-video-flow.md](references/ppt-podcast-video-flow.md). This is a HyperFrames composition branch, not NotebookLM native `video`.

1. **Resolve assets**
   - If the request includes PPT and podcast generation, run the PPT/slide branch and podcast branch first.
   - If the request says to use existing files or "刚刚生成的", resolve those files first and do not regenerate complete assets unnecessarily.
   - Accepted slide input: ordered slide images, a single image, PDF, PPT, or PPTX.
   - Accepted audio input: `.m4a`, `.mp3`, `.wav`, `.aac`, `.flac`, or `.ogg`.

2. **Build and render**
   - Use `scripts/run_ppt_podcast_video.py` as the default entrypoint.
   - Default command:
     ```bash
     python "{skill_dir}/scripts/run_ppt_podcast_video.py" \
       --slides-source "{slides_dir_or_pptx}" \
       --audio "{podcast_audio}" \
       --output-dir "{output_dir}" \
       --stem "{stem}" \
       --title "{video_title}"
     ```
   - Add `--transcript "{srt_or_vtt_or_json}"` when a transcript already exists.
   - Use `--no-render` only for tests or project inspection; user delivery should render MP4 by default.
   - The script runs `npx hyperframes transcribe` when no transcript is provided, then `lint`, `inspect`, and `render`.

3. **Report the package**
   - Return the final MP4 path, manifest path, HyperFrames project directory, slides directory, and transcript path when available.
   - If rendering fails, report the manifest path and the failed step. Do not report a completed video.

## WeChat Draft Layer

When the user asks to upload/create a WeChat Official Account draft, use the original `media-transfer` logic:

1. **Read or fetch the source**
   - Accept pasted text, local Markdown, Obsidian clippings, X/Twitter URLs, public web URLs, blog/newsletter links, and readable long-form documents.
   - Prefer a user-provided Markdown file when available.
   - If the user provides a URL, fetch readable article/post content with available web, browser, or source-specific tooling.
   - If PowerShell displays mojibake, reread files with explicit UTF-8 or use Python scripts that read UTF-8.

2. **Analyze and tear down the source**
   - Read the Content Diagnosis Markdown/JSON first when available.
   - Identify the original title strategy, opening hook, target reader, promise, narrative structure, examples, data points, CTA, and gaps.
   - Separate reusable ideas from wording that must not be copied.
   - Use diagnosis `core_insight`, `cognitive_gap`, `rewrite_angle`, and keep/drop/risk points to decide what should be preserved, reframed, removed, or strengthened.
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
   - If live `md2wechat --help` exposes `upload_image` and `create_draft`, upload the cover, build draft JSON with `scripts/make_wechat_draft_json.py`, and call `md2wechat create_draft <draft.json> --json`.
   - If live `md2wechat --help` exposes direct flags such as `--html`, `--markdown`, and `--cover` instead, publish the generated HTML/Markdown directly with that CLI and let it upload the cover and create the draft.
   - Report the returned WeChat draft `media_id`.

## Xiaohongshu Layer

When the user asks for Xiaohongshu output, generate a local 科普帖 package from the same analyzed source:

1. **Read and analyze the source**
   - Reuse the source reading rules from the WeChat draft layer.
   - Read the Content Diagnosis Markdown/JSON first when available.
   - Identify the original hook, target reader, reusable insight, emotional trigger, concrete scene, practical value, and what should be removed because it is too long-form or too technical for Xiaohongshu.
   - Use diagnosis content value, propagation value, cognitive gap, and Xiaohongshu platform strategy to choose the 科普 angle.

2. **Write a Xiaohongshu-ready 科普帖**
   - Default post type is `科普帖`; only use another type when the user explicitly asks.
   - Produce 3-5 title candidates. Prefer direct, curiosity-driven titles under 24 Chinese characters that promise one clear concept explanation.
   - Write one strong opening hook in the first 1-2 lines: name the common misunderstanding, surprising conclusion, or "why this matters".
   - Use an explainer structure instead of a generic opinion post: `先说结论` / `它到底是什么` / `为什么重要` / `常见误区` / `怎么判断或怎么用`.
   - Keep paragraphs short and concrete. Translate technical ideas into plain-language analogies, examples, checklists, or cause-effect chains.
   - Keep the tone platform-native: useful, specific, conversational, and easy to save or share. Do not copy the source wording.
   - Avoid hard-selling, empty emotional slogans, and unexplained jargon. If the source is technical, explain terms before making judgments.
   - Avoid pretending that tags are live platform rankings unless real platform research was performed in this session. Phrase them as "热门相关标签/发布建议标签".

3. **Generate tags and packaging**
   - Use `scripts/make_xiaohongshu_post.py` to package the final copy. Its default `post_type` is `科普帖`.
   - Provide at least 8 tags when possible: topic tags, audience tags, scenario tags, and content-format tags.
   - Create both `<stem>_xiaohongshu_post.md` and `<stem>_xiaohongshu_post.json`.
   - Include a cover suggestion: main cover line, secondary line, and visual direction.

4. **Report the package**
   - Return Markdown path and JSON path.
   - Include the selected recommended title and tag line in the final report.

## Combined Request Flow

When the user asks for podcast generation, PPT+podcast video, WeChat draft upload, and/or Xiaohongshu output in the same request:

1. Run the Content Diagnosis Layer once for the shared source and save `{stem}_content_diagnosis.md` plus `{stem}_content_diagnosis.json`.
2. Run the podcast layer and produce audio + title/description TXT + podcast cover JPG when requested, using the diagnosis podcast strategy.
3. Run requested NotebookLM artifact branches such as PPT/slides or mind map and produce visual files, not just Markdown.
4. If PPT+podcast video is requested, run the HyperFrames video layer after both slide and audio assets exist.
5. Run the WeChat draft layer from the same source using `media-transfer` analysis and rewrite logic when requested.
6. If useful, use the podcast title/description/cover as inputs or references for the WeChat article, but do not replace the media-transfer article analysis and rewrite.
7. Run the Xiaohongshu layer from the same source analysis when requested; keep it short-form and platform-native rather than a condensed WeChat article.
8. Upload the rewritten WeChat article draft using the unchanged `media-transfer` upload flow when requested.
9. Report all requested result groups: diagnosis Markdown/JSON, podcast package paths, video MP4/manifest paths, WeChat draft `media_id`, Xiaohongshu Markdown/JSON paths, and any NotebookLM artifact paths.

## Output Checklist

For content diagnosis, report:

- Diagnosis Markdown path.
- Diagnosis JSON path.
- Content value and propagation value.
- Recommended rewrite angle.
- Podcast strategy title when podcast was requested.

For NotebookLM artifact output, report:

- NotebookLM source/notebook used, when available.
- State JSON path and log path when run in background.
- Requested kind and actual generation method.
- Source IDs.
- Artifact ID when NotebookLM exposes one.
- PPT design prompt file path for slide requests.
- Final visual output path for PPT and mind map requests.
- Intermediate Markdown path only as supporting evidence, not as the completed PPT/mind-map deliverable.

For podcast-layer output, also report:

- Audio path.
- Title/description TXT path.
- Cover JPG path.

For PPT+podcast-video output, also report:

- Final MP4 path.
- Video manifest path.
- HyperFrames project directory.
- Slides image directory.
- Transcript path when available.

For WeChat-draft-layer output, report:

- Source read/fetch status.
- Analysis/rewrite status.
- Rewritten Markdown path, when saved.
- WeChat HTML path and draft JSON path.
- WeChat draft `media_id`.
- Whether the audio was embedded or only referenced, based on live capability evidence.

For Xiaohongshu-layer output, report:

- Xiaohongshu Markdown path.
- Xiaohongshu JSON path.
- Recommended title.
- Related hashtag line.
- Cover suggestion.

## Local Resource Map

NotebookLM/source utilities copied from `qiaomu-anything-to-notebooklm`:

- `scripts/fetch_url.sh`
- `scripts/get_podcast_transcript.py`
- `scripts/run_notebooklm_artifact.py`
- `scripts/run_notebooklm_podcast.py`
- `scripts/run_ppt_podcast_video.py`
- `scripts/make_podcast_cover.py`
- `scripts/make_podcast_info.py`
- `scripts/make_content_diagnosis.py`
- `scripts/make_xiaohongshu_post.py`

Optional podcast-to-WeChat wrapper helper, only for requests that explicitly need a Markdown wrapper around generated podcast assets:

- `scripts/build_podcast_wechat_markdown.py`

Publishing utilities copied from `media-transfer`:

- `scripts/publish_markdown_to_wechat.py`
- `scripts/make_wechat_draft_json.py`
- `scripts/New-LocalWechatCover.ps1`

Detailed references:

- [references/content-diagnosis-flow.md](references/content-diagnosis-flow.md)
- [references/notebooklm-artifact-flow.md](references/notebooklm-artifact-flow.md)
- [references/ppt-design-module.md](references/ppt-design-module.md)
- [references/notebooklm-podcast-flow.md](references/notebooklm-podcast-flow.md)
- [references/ppt-podcast-video-flow.md](references/ppt-podcast-video-flow.md)
- [references/wechat-flow.md](references/wechat-flow.md)

## Common Failure Modes

- Content diagnosis missing: if a readable source exists and the request is not direct conversion or asset-only composition, create `{stem}_content_diagnosis.md` and `{stem}_content_diagnosis.json` before claiming downstream outputs are complete.
- Generic podcast output: if NotebookLM audio was generated with default generic instructions while a diagnosis existed, rerun or regenerate with diagnosis-driven `--instructions`.
- NotebookLM artifact CLI missing: install `nlm` with `go install github.com/tmc/nlm/cmd/nlm@latest`, or run the artifact script with `--install-nlm`.
- NotebookLM podcast CLI missing: install `notebooklm-py[cookies]` or run the podcast script with `--install-notebooklm-py`.
- NotebookLM login missing: run `nlm auth <Chrome profile name>` and verify with `nlm notebook list`. For multi-account Chrome profiles, use `NLM_AUTHUSER` or the script's `--authuser`.
- Podcast cookie auth missing: run `notebooklm login --browser-cookies chrome` after installing `notebooklm-py[cookies]`; this keeps podcast generation/download in the terminal while reusing the already logged-in Chrome account.
- `nlm audio download` says Google CDN requires browser session cookies: do not let the job poll that path forever. Use the default `notebooklm-py` podcast backend instead.
- Podcast runtime clutter: `run_notebooklm_podcast.py` writes state/log files to a hidden sibling `.media-writer-runtime` directory by default. Do not move those runtime files back into the user-facing delivery folder.
- macOS vs Windows mismatch: treat it as an environment/tooling mismatch, not a product workflow difference. Both systems should use `nlm` CLI once installed and authenticated.
- PPT+podcast video render fails: inspect `{stem}_video_manifest.json` first. The video script records `lint`, `inspect`, `render`, and `doctor` outputs when HyperFrames fails.
- PPT+podcast video cannot export PPT/PDF slides: install LibreOffice/soffice for PPT/PPTX export and `pdftoppm` for PDF-to-image conversion, or pass an ordered slide image directory.
- PPT local export missing: `nlm create-slides` may expose a NotebookLM slide artifact without a local PPTX/PDF downloader. Report the artifact details and notebook ID instead of inventing a file.
- PPT native fallback: when `nlm create-slides` fails or lacks download support, use the Markdown draft as content input for a rendered `.pptx`; do not stop at Markdown.
- Mind map opens browser: `nlm mindmap` may create an interactive NotebookLM mind map and save it as a note. Still run it from CLI and save stdout/note evidence, but render `.png`/`.svg` if no directly viewable map file is available.
- PowerShell displays mojibake: prefer UTF-8 file reads and Python scripts; verify bytes or output files when display encoding looks wrong.
- `md2wechat` image generation credentials fail: use `scripts/make_podcast_cover.py` or `scripts/New-LocalWechatCover.ps1`.
- `md2wechat` command surface differs: inspect live `md2wechat --help`. Some installs expose `upload_image/create_draft`; Python package installs may expose direct publish flags only.
- WeChat `40125 invalid appsecret`: verify the credential source the live `md2wechat` actually reads. Direct-publish Python installs read `.env`/environment variables and may ignore a newer `md2wechat.yaml`.
- WeChat `40164 invalid ip`: ask the user to add the reported IP to the Official Account IP whitelist, then retry.
- WeChat `41039 invalid content_source_url`: keep `content_source_url` empty or use a real `https://...` URL; never pass local file paths as source URLs.
- Audio cannot be embedded: do not invent a public audio URL. Report the audio path and explicitly state the audio is referenced rather than embedded.
