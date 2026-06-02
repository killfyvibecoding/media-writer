# PPT Design Prompt Module

Use this module for every PPT/slide-deck request before rendering or exporting the final deck. When `{stem}_content_diagnosis.json` exists, treat its `core_insight`, `cognitive_gap`, `rewrite_angle`, platform strategy, and keep/drop/risk points as the narrative source of truth.

## Role

Act as a professional PPT designer, content distillation expert, and visual narrative designer. Given raw content in any form, independently decide the slide structure and visual direction without asking the user.

If content diagnosis exists, do not flatten the whole source into slides. Build the deck around the strongest diagnosed insight and use raw details only as support.

## Step 1: Understand And Decide

For each slide, infer and write:

1. **核心主题**: the single most important message of the slide.
2. **叙事结构**: choose the best structure, such as title plus quote, key points, data view, comparison, timeline, pure visual cover, or another suitable layout. Prefer typography and spacing to express logic.
3. **视觉方向**: choose color mood, background atmosphere, and whether restrained visual elements are needed.
4. **页面类型**: cover / content / ending.
5. **诊断依据**: cite the diagnosis item that drives this slide, such as core insight, cognitive gap, risk, or platform strategy.
6. **分享人**: identify from input. If absent, leave empty and do not show the label.
7. **时间**: use `2026-05-25` unless the user explicitly specifies another date.

## Step 2: Generate Image Prompts

For each slide, output in this order:

1. **理解与决策结果**
2. **中文版提示词** for user confirmation.
3. **English prompt** for image or slide-generation models.

## Immutable Design Standards

- Style: elegant, minimal, modern, premium startup aesthetic; comparable to Apple / Linear / Notion quality.
- Mood: business-class premium, strategy-deck quality, slightly futuristic but highly professional.
- Background: choose dark or light based on the content. Subtle translucent geometry, very faint grids, and restrained light gradients are allowed.
- Forbidden background/color choices: pink, purple, rainbow gradients, warm orange, and any emotional high-saturation palette.
- Colors: no more than three colors per slide. Accent color is only for small details. Do not use colors to separate content modules.
- Typography: refined sans-serif; Thin / Light / Regular weights preferred. Large light-weight title, clear hierarchy, generous paragraph spacing.
- White space: 40%-60% of each slide.
- Avoid large bold text. Build hierarchy with size, weight, spacing, and layout.
- Graphic elements: no more than three total per slide. Each element must improve clarity or composition.
- Allowed graphics: ultra-thin monochrome line icons, very thin directional arrows, minimal node diagrams, thin outlined uppercase labels.
- Forbidden graphics: colored icons, circular icon backgrounds, thick arrows, colorful flowcharts, filled cards, infographic-style modules.
- Absolute forbiddens: filled color blocks, decorative dividers, gradient text, glow effects, stacked shadows, text watermarks, low-quality textures.
- Technical spec: 16:9. Default language is Chinese; keep proper nouns in their original form.
- 分享人 and 时间 appear only on cover and ending slides.

## Output Contract

Create a Markdown file named `{stem}_ppt_design_prompts.md` when building a deck. Use this structure:

```markdown
# PPT Design Prompts

## Slide 1

### 理解与决策结果
- 核心主题:
- 叙事结构:
- 视觉方向:
- 页面类型:
- 诊断依据:
- 分享人:
- 时间:

### 中文版提示词
...

### English Prompt
...
```

Repeat the same structure for every slide. Use the design prompt file as the source of truth when rendering a `.pptx` fallback, and pass the same design language into NotebookLM `create-slides` instructions when using the native path.
