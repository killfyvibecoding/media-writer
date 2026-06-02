# NotebookLM Artifact Flow

Use this reference for NotebookLM outputs other than the podcast package: PPT/slide deck, mind map, video, report, quiz, flashcards, infographic brief, data table, summary, outline, FAQ, study guide, briefing document, timeline, and table of contents.

## Source Routing

Use the same source rules as the podcast flow:

| Input | Route |
| --- | --- |
| YouTube URL | Add the URL directly to NotebookLM. Do not use yt-dlp, browser automation, Whisper, or subtitle download. |
| Public web URL | Prefer direct NotebookLM URL ingestion. |
| `x.com` or `twitter.com` | Try direct NotebookLM ingestion first; if blocked, fetch readable text and add the Markdown/TXT. |
| `xiaoyuzhoufm.com`, `ximalaya.com`, `bilibili.com` | Use transcript extraction only when NotebookLM cannot ingest the link directly or the user needs transcript fidelity. |
| Local `.md`/`.txt`/PDF/DOCX/PPTX | Add directly when `nlm source add` accepts it; otherwise convert to Markdown/TXT first. |
| Multiple sources | Add each source to the same notebook, then generate one combined artifact. |
| Search query | Search, summarize 3-5 relevant sources into one Markdown/TXT source, then add it. |

When a readable source exists, create `{stem}_content_diagnosis.md` and `{stem}_content_diagnosis.json` first with [content-diagnosis-flow.md](content-diagnosis-flow.md). Use that diagnosis to shape PPT, mind map, report, and study artifact instructions.

## CLI-First Sequence

Use the same background CLI workflow on macOS, Windows, and Linux. Browser interaction is only for one-time Google login or when the CLI cannot operate.

```bash
go install github.com/tmc/nlm/cmd/nlm@latest
nlm auth "<Chrome profile name>"
nlm notebook list
```

Preferred script entrypoint:

```bash
python "{skill_dir}/scripts/run_notebooklm_artifact.py" \
  --source "{source_path_or_url}" \
  --output-dir "{output_dir}" \
  --title "{notebook_title}" \
  --stem "{stem}" \
  --kind slides \
  --auth-profile "{Chrome profile name}" \
  --install-nlm \
  --background
```

For multiple sources, repeat `--source`:

```bash
python "{skill_dir}/scripts/run_notebooklm_artifact.py" \
  --source "{article_url}" \
  --source "{youtube_url}" \
  --source "{local_pdf}" \
  --output-dir "{output_dir}" \
  --title "{notebook_title}" \
  --stem "{stem}" \
  --kind mindmap \
  --background
```

The script writes:

- `{stem}.notebooklm-artifact.state.json`
- `{stem}.notebooklm-artifact.log` when run with `--background`
- One output file, depending on `--kind`

Use the state JSON and log for progress checks. Do not open NotebookLM in a browser unless the state/log shows a real CLI blocker or the user explicitly asks for visual inspection.

## Artifact Kinds

| User wording | `--kind` | Native path |
| --- | --- | --- |
| 做成PPT, 生成幻灯片, 做个演示 | `slides` | `nlm create-slides`; deliver native export or rendered `.pptx` |
| 思维导图, 脑图, 导图 | `mindmap` | `nlm mindmap`; deliver native map or rendered `.png`/`.svg` |
| 做个视频, 生成视频 | `video` | `nlm create-video` then `nlm video download` |
| 生成报告, 整理成文档 | `report` | `nlm create-report`; save `artifact get` details |
| 总结 | `summary` | `nlm summarize` |
| 大纲 | `outline` | `nlm outline` |
| FAQ | `faq` | `nlm faq` |
| 学习指南 | `study-guide` | `nlm study-guide` |
| 简报文档 | `briefing-doc` | `nlm briefing-doc` |
| 时间线 | `timeline` | `nlm timeline` |
| 目录 | `toc` | `nlm toc` |
| Quiz/测验 | `quiz` | `nlm generate-chat`; save Markdown |
| 闪卡/记忆卡片 | `flashcards` | `nlm generate-chat`; save Markdown |
| 信息图/可视化 | `infographic` | `nlm generate-chat`; save Markdown brief |
| 数据表/表格 | `data-table` | `nlm generate-chat`; save Markdown table |

Treat live `nlm --help` output as the authority. If the installed CLI later adds native download support for PPT/PDF, use it and report the produced file path.

## PPT / Slide Deck Notes

Current `nlm` exposes `create-slides <notebook-id> <instructions>` and `artifact list/get`. It may not expose direct PPTX/PDF download. Therefore:

1. Create the notebook.
2. Add all sources.
3. Read the content diagnosis JSON, then read [ppt-design-module.md](ppt-design-module.md) and create `{stem}_ppt_design_prompts.md`.
4. The design prompt file must contain, for each slide, `理解与决策结果`, `中文版提示词`, and `English Prompt` in that order.
5. Run `nlm create-slides` with instructions that preserve the diagnosis `core_insight`, `rewrite_angle`, and the same premium, minimal, Apple/Linear/Notion-style visual direction.
6. Poll `nlm --json artifact list`.
7. Save `nlm artifact get <artifact-id>` to `{stem}_slides_artifact.txt`.
8. Report the design prompt file, NotebookLM artifact ID, and details file.
9. If `nlm create-slides` returns `bad-args` while the notebook/source are valid, fall back to `nlm generate-chat` and save a Markdown slide draft to `{stem}_slides.md`, with `method` and `native_error` recorded in state JSON.
10. Treat that Markdown as intermediate content. Render a real `.pptx` with the presentations workflow before marking the PPT request complete.

Do not claim a local `.pptx` or `.pdf` exists unless a command created that file.

### PPT Design Prompt Rules

For PPT requests, the design layer is mandatory. Do not ask the user to choose a style unless they already provided one. Decide the slide type, narrative structure, color mood, visual hierarchy, sharing person, and date from the source. Use `2026-05-25` unless the user explicitly specified another date.

The visual style must be elegant, minimal, modern, and premium startup oriented. Avoid pink, purple, rainbow gradients, warm orange, high-saturation palettes, filled cards, infographic-style modules, gradient text, glow effects, stacked shadows, and decorative dividers. Use at most three colors per slide, thin/light/regular sans-serif typography, and 40%-60% white space.

Share person and time appear only on cover and ending slides. If no share person is present, leave it empty and omit the label in the rendered slide.

## Mind Map Notes

Current `nlm` exposes `mindmap <notebook-id> <source-id> [source-id...]`. It may open or reference the interactive NotebookLM map and says the map is also saved as a note.

1. Create the notebook.
2. Add all sources.
3. Use the content diagnosis to choose the hierarchy: core insight, supporting logic, examples, risks, then actions/platform implications.
4. Read source IDs with `nlm --json source list <notebook-id>`.
5. Run `nlm mindmap <notebook-id> <source-id>...`.
6. Save stdout to `{stem}_mindmap.md`. If stdout is empty, save a short evidence note and keep the state JSON with source IDs.
7. If `nlm mindmap` returns `bad-args` while `nlm source-guide` or `nlm generate-chat` can read the same notebook, treat it as an `nlm` ActOnSources/RPC limitation. Fall back to `nlm generate-chat` and save a Markdown mind-map draft, with `method` and `native_error` recorded in state JSON.
8. Treat that Markdown as intermediate content. Render a viewable `.png`/`.svg` before marking the mind-map request complete.
9. If the user needs native NotebookLM visual verification, use browser automation only after CLI generation succeeds or fails with a UI-only blocker.

The same fallback rule applies to `summary`, `outline`, `faq`, `study-guide`, `briefing-doc`, `timeline`, and `toc`: try the native `nlm` command first, then use `generate-chat` when the native command fails on a valid notebook/source.

## Raw Commands

```bash
notebook_id="$(nlm notebook create "{notebook_title}" | sed -nE 's/.*([0-9a-f-]{36}).*/\1/p' | head -1)"
nlm source add --name "{source_title}" "$notebook_id" "{source_path_or_url}"
nlm --json source list "$notebook_id"
nlm create-slides "$notebook_id" "{instructions}"
nlm --json artifact list "$notebook_id"
nlm artifact get "{artifact_id}" > "{output_dir}/{stem}_slides_artifact.txt"
```

For mind maps:

```bash
nlm mindmap "$notebook_id" "{source_id_1}" "{source_id_2}" > "{output_dir}/{stem}_mindmap.md"
```

## Output Report

Always report:

- Requested kind.
- Notebook ID.
- Source IDs.
- State JSON path.
- Log path if backgrounded.
- Artifact ID when available.
- PPT design prompt file for slide requests.
- Final visual output path for PPT and mind-map requests.
- Intermediate Markdown path when fallback content was used.
- Whether the final output is native NotebookLM visual output or a rendered visual deliverable built from Markdown fallback content.
