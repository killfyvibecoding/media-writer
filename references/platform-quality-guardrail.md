# Platform Quality Guardrail

Use this module after content diagnosis and before WeChat, Xiaohongshu, podcast-script, PPT copy, or visual-cover copy generation when the source is readable.

## Source Rules

This guardrail distills two recurring platform lessons:

1. Low-creation-degree content loses recommendation because it is homogeneous, copied, stitched, low-information, or low-value AIGC.
2. WeChat accounts lose distribution when they repeatedly touch risky topics, private-domain diversion, copied material, unauthorized images, abnormal engagement, excessive marketing, or AI-flavored repetitive updates.

The goal is not to make every article conservative. The goal is to preserve the source insight while adding enough original judgment, structure, examples, and platform-safe phrasing.

## Required Checks

Create `{stem}_platform_quality_guardrail.md` and `{stem}_platform_quality_guardrail.json` with `scripts/make_platform_quality_guardrail.py`.

Check at least these dimensions:

- **Homogeneity**: repeated title/cover/body frames, batch-like formats, no information increment.
- **Copying / washing / stitching**: large paraphrase blocks, screenshots as main content, source reordering without original analysis.
- **Low information**: generic statements, unsupported claims, image-text mismatch, no examples or useful framework.
- **Low-value AIGC**: obvious template phrasing, direct AI output, excessive neatness without personal judgment.
- **Sensitive / distribution risk**: high-pressure topics, direct calls to private traffic, QR codes, external links, hard-selling, abnormal engagement tactics.
- **Asset risk**: reused web images, unclear license, generated images with broken logic and no explanation.

## Packaging Command

```bash
python "{skill_dir}/scripts/make_platform_quality_guardrail.py" \
  --topic "{topic}" \
  --source "{source_path_or_url}" \
  --verdict "{overall quality verdict}" \
  --risk-level medium \
  --low-creation-score 6 \
  --distribution-risk-score 7 \
  --check "搬运洗稿::high::直接复述原文风险高::重构为原创判断框架" \
  --check "低价值AIGC::medium::容易套用万能排比::加入具体场景和反例" \
  --must-do "加入原创判断" \
  --must-do "给出可验证案例或使用场景" \
  --must-avoid "直接拼接原文段落" \
  --must-avoid "二维码、加微信、扫码领资料等私域诱导" \
  --platform-rule "微信::标题克制，正文有原创增量、引用边界和风险提示" \
  --platform-rule "小红书::做成科普帖或经验帖，不做伪干货和焦虑标题" \
  --rewrite-strategy "先提炼核心判断，再用新结构重写，最后做低创作度自检" \
  --post-check "标题不夸大承诺" \
  --post-check "正文不复读原文" \
  --post-check "无私域诱导或盗图风险" \
  --markdown "{output_dir}/{stem}_platform_quality_guardrail.md" \
  --json "{output_dir}/{stem}_platform_quality_guardrail.json"
```

## Branch Consumption

### WeChat

- Read the guardrail before writing.
- Do not copy source paragraphs as the new body.
- Add original judgment, concrete examples, practical structure, and safe risk phrasing.
- Avoid QR-code language, private-domain hooks, copied images, hard-selling, and sensitive-topic escalation.
- After writing, self-check title, opening, originality, source use, CTA, image use, and sensitive phrasing.

### Xiaohongshu

- Use a platform-native explainer or experience-card structure.
- Avoid pseudo-useful lists that only rename the source.
- Keep one clear concept, one concrete scene, and one save-worthy checklist.
- Tags are suggestions unless live platform research was performed.

### Podcast

- Do not read the source as a summary.
- Use the guardrail to add discussion, objections, examples, and risk notes.
- Avoid turning financial, medical, legal, education, or policy sources into advice.

### Visual Assets

- Do not use recycled stock-like covers or generated images that do not logically follow the article.
- Use original diagnosis-driven image prompts and label fallback covers clearly.

## Failure Policy

- If the guardrail score is high or critical, generation can continue only with explicit mitigation in the branch output.
- If the source is mostly copied or low-information, generate a rewrite around the useful insight rather than a paraphrase.
- If the output still reads like a template, rewrite it before upload.
