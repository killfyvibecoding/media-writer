# PPT Podcast Video Flow

Use this reference when the user asks to turn PPT/slides plus podcast/audio into a dynamic MP4 video. This is separate from NotebookLM native `video` artifacts.

## Trigger Wording

Run this branch when the request mentions both slide/PPT material and podcast/audio/video synthesis:

- `PPT和播客合成视频`
- `把PPT配播客做成视频`
- `生成PPT、播客、视频`
- `用现有PPT和播客生成视频`
- `用刚刚生成的PPT和播客做成视频`

Do not use this branch for a plain `生成视频` request with no PPT/podcast context; that remains the NotebookLM native `video` artifact path.

## Defaults

- Implementation: HyperFrames-first.
- Style: strong narrative dynamic only.
- Aspect ratio: 16:9 landscape.
- Audio: podcast audio is the master timeline.
- Captions: full captions plus keyword emphasis overlays.
- Output behavior: render final MP4 directly.
- Fallback: do not silently downgrade to ffmpeg. Diagnose and report HyperFrames failures.

## Required Inputs

The script accepts:

- `--slides-source`: directory of ordered images, one image, PDF deck, or PPT/PPTX deck.
- `--audio`: podcast audio path.
- `--output-dir`: video package directory.
- `--stem`: output filename stem.
- `--transcript`: optional SRT/VTT/JSON transcript.
- `--no-render`: create project and manifest without rendering, for tests or previews only.

Preferred command when PPT and podcast already exist:

```bash
python "{skill_dir}/scripts/run_ppt_podcast_video.py" \
  --slides-source "{slides_dir_or_pptx}" \
  --audio "{podcast_audio}" \
  --transcript "{optional_transcript}" \
  --output-dir "{output_dir}" \
  --stem "{stem}" \
  --title "{video_title}"
```

For tests or project inspection without rendering:

```bash
python "{skill_dir}/scripts/run_ppt_podcast_video.py" \
  --slides-source "{slides_dir_or_pptx}" \
  --audio "{podcast_audio}" \
  --transcript "{optional_transcript}" \
  --output-dir "{output_dir}" \
  --stem "{stem}" \
  --no-render
```

## Combined Request Sequence

When the user asks for PPT, podcast, and video in the same request:

1. Run the PPT/slide branch first and produce a real visual deck or exportable slide image source.
2. Run the podcast branch and produce the audio file.
3. Run this video branch with the PPT/slide output and podcast audio.
4. Report the final MP4 plus manifest/transcript/project paths.

When the user asks to use existing PPT and podcast:

1. Resolve explicit user paths first.
2. If no explicit paths are provided, locate the newest relevant outputs from the current run.
3. Do not regenerate PPT or podcast unless the user asks to fill missing assets.

## Motion Requirements

The output must not be static slide playback. Each slide should use strong narrative motion:

- Multi-shot treatment per slide.
- Push into the title or key visual region.
- Pan toward important content.
- Local crop/zoom emphasis.
- Keyword overlays timed to transcript.
- Thin-line nodes, route marks, or structure lines where useful.
- Narrative transitions between slides.

Avoid:

- Random effects.
- Flashy template transitions.
- Neon/glow-heavy looks.
- Equalizer bars or generic waveform visuals.
- Overcrowded captions and keyword overlays at the same time.

## Outputs

Report:

- `{stem}_video.mp4`
- `{stem}_video_manifest.json`
- `{stem}_transcript.srt` or `.vtt` when available
- `{stem}_video_project/`
- `{stem}_slides/`

The manifest is the durable status record. If render fails, report the manifest path and failure fields.

## Failure Handling

- If HyperFrames render fails, run `npx hyperframes doctor` through the script diagnostics.
- Do not claim completion when the MP4 is missing or empty.
- Do not silently create a lower-quality ffmpeg-only video.
- If slide export from PPT/PPTX fails, report whether LibreOffice/soffice or `pdftoppm` is missing.
