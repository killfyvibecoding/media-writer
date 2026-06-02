# Content Diagnosis Flow

Use this flow before generating podcast, WeChat, Xiaohongshu, PPT, mind map, or other media outputs from a readable source.

## Goal

Diagnose the source as a media asset before rewriting or packaging it. The diagnosis decides what is worth keeping, what should be weakened, which platform angle is strongest, and how the podcast should sound.

This layer borrows the practical logic of dbskill-style content diagnosis:

- Separate **content value** from **propagation value**.
- Fix the topic, hook, expression efficiency, and cognitive gap before writing.
- Detect fuzzy concepts, false assumptions, AI-smooth writing, and weak platform fit.
- Convert raw information into platform-native strategy instead of summarizing the source.

## Required Outputs

For a source with stem `{stem}`, create these two files before other generated outputs when source content is available:

- `{stem}_content_diagnosis.md`
- `{stem}_content_diagnosis.json`

Use `scripts/make_content_diagnosis.py` to package the files after making the diagnosis.

## Diagnosis Checklist

1. **Source thesis**: what the source is really saying.
2. **Content value**: whether the idea is useful, timely, concrete, non-obvious, or has reusable knowledge.
3. **Propagation value**: whether the idea has a hook, tension, audience pain, contrast, authority, story, or save/share reason.
4. **Five dimensions**:
   - 文字洁癖: remove vague, decorative, over-smooth, or AI-flavored language.
   - 标题/封面/开头: check whether there is a clear topic, hook, and credibility signal.
   - 表达效率: compress detours, jargon, and repeated framing.
   - 认知落差: identify the gap between what readers assume and what the source proves.
   - 平台适配/AI辅助: decide what each platform should emphasize or avoid.
5. **Concept traps**: find undefined terms, false choices, category confusion, and unsupported causal claims.
6. **Material strength**: list usable data, cases, quotes, scenes, authority signals, and concrete examples.
7. **Keep / drop / risk**: decide what must remain, what should be weakened, and what requires caution.

## Packaging Command Shape

```bash
python "{skill_dir}/scripts/make_content_diagnosis.py" \
  --topic "{topic}" \
  --source "{source_path_or_url}" \
  --verdict "{overall judgement}" \
  --content-value 8 \
  --propagation-value 7 \
  --priority "高" \
  --core-insight "{one-sentence insight}" \
  --cognitive-gap "{reader assumption vs source insight}" \
  --rewrite-angle "{recommended angle}" \
  --dimension "文字洁癖::可改进::删掉空泛判断，保留具体案例" \
  --dimension "标题/封面/开头::需要强化::补一个认知冲突式开场" \
  --platform "微信::高::长文解释底层逻辑和方法论" \
  --platform "小红书::中高::科普一个反直觉判断" \
  --platform "播客::中高::用对话讲清价值、边界和误区" \
  --keep "{must keep}" \
  --drop "{should weaken}" \
  --risk "{risk note}" \
  --podcast-angle "{podcast angle}" \
  --podcast-listener "{listener profile}" \
  --podcast-hook "{opening hook}" \
  --podcast-tone "{tone}" \
  --podcast-title "{title}" \
  --podcast-description "{description}" \
  --podcast-cover-direction "{cover direction}" \
  --podcast-point "{must cover point}" \
  --markdown "{output_dir}/{stem}_content_diagnosis.md" \
  --json "{output_dir}/{stem}_content_diagnosis.json"
```

The script validates required fields and writes both human-readable Markdown and machine-readable JSON. Use the JSON as the cross-branch source of truth when possible.

## Branch Consumption

### Podcast

Use `podcast_strategy` from the diagnosis to build NotebookLM `--instructions`.

The instructions should specify:

- angle and listener profile
- opening hook
- must-cover points
- weak/skip points
- tone
- risk notes if the source touches finance, medical, legal, policy, or market claims

Use the diagnosis title, description, and cover direction for the podcast info TXT and cover generation.

### WeChat

Use `core_insight`, `cognitive_gap`, `rewrite_angle`, and `keep/drop/risk` to rewrite the article. The WeChat draft should become a new article with a stronger topic and structure, not a summary of the source.

### Xiaohongshu

Use the diagnosis to choose a 科普帖 angle. Prefer curiosity gap, cognitive conflict, save-worthy explanation, and plain-language examples. Keep tags related, but do not claim they are live trending data unless platform research was actually performed.

### PPT

Use `core_insight`, `rewrite_angle`, and the five-dimension diagnosis as input to `ppt-design-module.md`. Slide prompts should express the strongest narrative, not all raw details.

### Mind Map

Use the diagnosis to choose the hierarchy: core insight first, then supporting logic, examples, risks, and platform/action branches. Avoid turning the source into a flat outline.

## Failure Policy

- If the source is unreadable, stop and report the read failure.
- If the source is weak but readable, do not block generation. Write the weakness into the diagnosis, choose the best salvage angle, and continue.
- If the requested output uses an existing finished asset without a source, diagnosis is optional; do not invent source analysis.
