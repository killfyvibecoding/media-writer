# Visual Generation Module

Use this module when `media-writer` needs covers, first images, article illustrations, PPT visual prompts, information graphics, or any diagnosis-driven image prompt package.

## Core Rule

Generate visuals from the content diagnosis, not from a fixed template. A strong visual asset must pass three checks:

1. **Logical**: the image promise follows from the source, not clickbait.
2. **Attractive**: the first-view hook creates curiosity, contrast, emotion, or usefulness.
3. **Reusable**: the image and prompt file can be used independently outside the current branch.

## Diagnosis Inputs

Prefer `visual_strategy` from `{stem}_content_diagnosis.json`:

- `fit_score`: 0-10 visual suitability.
- `explosive_potential`: why the asset could attract attention or become save/share-worthy.
- `logic_check`: why the visual framing is true to the source.
- `audience_hook`: first-view hook.
- `style_keywords`: style hints.
- `metaphors`: concrete visual metaphors.
- `avoid`: visual traps to avoid.
- `asset_suggestions`: suggested assets and directions.

If an older diagnosis lacks `visual_strategy`, infer these fields from `content_value`, `propagation_value`, `core_insight`, `cognitive_gap`, `rewrite_angle`, and platform strategies.

## Asset Types

| Asset | Aspect | Best Use |
| --- | --- | --- |
| `wechat-cover` | 16:9 | Official Account draft cover |
| `podcast-cover` | 16:9 | Podcast audio package cover |
| `xiaohongshu-cover` | 3:4 | Xiaohongshu first image / save-worthy card |
| `ppt-cover` | 16:9 | Premium deck title slide prompt |
| `article-illustration` | 16:9 | Inline image for concept/story explanation |
| `infographic` | 3:4 | High-density summary image |

## Style Selection

Use the `baoyu-skills` dimension model as the selection vocabulary:

- Cover type: `hero`, `conceptual`, `typography`, `metaphor`, `scene`, `minimal`.
- Palette: `warm`, `elegant`, `cool`, `dark`, `earth`, `vivid`, `pastel`, `mono`, `retro`, `duotone`, `macaron`.
- Rendering: `flat-vector`, `hand-drawn`, `painterly`, `digital`, `pixel`, `chalk`, `screen-print`.
- Text: `none`, `title-only`, `title-subtitle`, `text-rich`.
- Mood: `subtle`, `balanced`, `bold`.
- Font: `clean`, `handwritten`, `serif`, `display`.

Recommended mappings:

| Content Signal | Type | Palette | Rendering | Preset |
| --- | --- | --- | --- | --- |
| AI / tech / infrastructure | `conceptual` | `cool` | `digital` | `blueprint` |
| Business / strategy / market | `metaphor` | `elegant` | `screen-print` | `editorial` |
|人物 / story / history | `scene` | `warm` or `retro` | `hand-drawn` or `digital` | `warm` / `retro` |
| Knowledge / explainer | `conceptual` | `macaron` | `hand-drawn` | `hand-drawn-edu` |
| Warning / crisis / avoid mistakes | `typography` | `dark` | `screen-print` | `poster-art` |
| Essential / minimal / premium | `minimal` | `mono` | `flat-vector` | `minimal` |

## Prompt Pack Command

```bash
python "{skill_dir}/scripts/make_visual_prompt_pack.py" \
  --diagnosis-json "{output_dir}/diagnosis/{stem}_content_diagnosis.json" \
  --output-dir "{output_dir}/visual" \
  --stem "{stem}" \
  --asset wechat-cover \
  --asset podcast-cover \
  --asset xiaohongshu-cover \
  --markdown "{output_dir}/visual/{stem}_visual_prompt_pack.md" \
  --json "{output_dir}/visual/{stem}_visual_prompt_pack.json"
```

The script writes:

```
visual/
├── {stem}_visual_prompt_pack.md
├── {stem}_visual_prompt_pack.json
└── prompts/
    ├── 01-wechat-cover.md
    ├── 02-podcast-cover.md
    └── 03-xiaohongshu-cover.md
```

## Raster Generation Policy

- Write prompt files first. They are the source of truth.
- Use a real raster image backend only when available and requested.
- If using a generated bitmap with rendered text, do not patch text by drawing over the image. Regenerate with a corrected prompt or use less text.
- If no raster backend is available but a cover is required immediately, use `scripts/make_podcast_cover.py` as a local text-led fallback and label it as fallback.

## Local Fallback Themes

`scripts/make_podcast_cover.py` supports these themes:

| Theme | Use |
| --- | --- |
| `tech-blueprint` | AI, chips, infrastructure, systems |
| `business-story` | founders, strategy, company stories |
| `knowledge-card` | explainer, framework, Xiaohongshu-like knowledge cover |
| `warm-human` | emotion, life, personal story |
| `dark-cinematic` | high-drama narrative, warning, history |
| `minimal-mono` | premium minimal thesis |
| `editorial` | opinion, media, analysis |
| `ai-infra` | default AI infrastructure and tech-business cover |

Fallback covers are useful but not a replacement for diagnosis-driven image prompts when the user asks for rich generated visuals.
