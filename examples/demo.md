# Demo

下面是一个典型任务示例。

## 输入

```text
使用 $media-writer 处理 D:\notes\AI-agent-report.md：
生成播客、微信公众号草稿和小红书科普帖。
```

## Agent 应执行的流程

1. 读取 `AI-agent-report.md`。
2. 生成内容诊断：
   - 判断内容价值和传播价值；
   - 输出五维诊断；
   - 生成播客策略、微信改写角度和小红书科普角度；
   - 保存 `*_content_diagnosis.md` 和 `*_content_diagnosis.json`。
3. 播客分支按诊断策略执行：
   - 创建或复用 NotebookLM notebook；
   - 添加 source；
   - 用诊断里的 `podcast_strategy` 生成 audio overview；
   - 下载音频；
   - 生成标题简介 TXT；
   - 生成播客封面 JPG。
4. 微信草稿分支按诊断策略执行：
   - 重构标题、开头、结构和读者承诺；
   - 写一篇新的微信文章；
   - 转换为 WeChat HTML；
   - 上传封面；
   - 生成 draft JSON；
   - 创建微信公众平台草稿。
5. 小红书分支按诊断策略执行：
   - 生成科普帖标题候选；
   - 写解释型正文；
   - 生成热门相关标签和封面建议；
   - 保存 Markdown 和 JSON。

## 示例输出目录

```text
outputs/ai-agent-report/
├── diagnosis/
│   ├── ai-agent-report_content_diagnosis.md
│   └── ai-agent-report_content_diagnosis.json
├── podcast/
│   ├── ai-agent-report.m4a
│   ├── ai-agent-report_podcast_info.txt
│   └── ai-agent-report_podcast_cover.jpg
├── wechat/
│   ├── ai-agent-report_wechat_rewrite.md
│   ├── ai-agent-report_wechat_rewrite.wechat.html
│   ├── ai-agent-report_wechat_rewrite.image-map.json
│   ├── ai-agent-report_wechat_rewrite.draft.json
│   └── ai-agent-report_draft_result.json
└── xiaohongshu/
    ├── ai-agent-report_xiaohongshu_post.md
    └── ai-agent-report_xiaohongshu_post.json
```

## 播客标题简介示例

```text
标题：
AI会把你放大成谁

简介：
这一期从一篇长文出发，聊 AI 如何放大人的判断、品位、组织能力和信任关系。我们会拆解一人公司、组织中部坍塌，以及为什么智能时代真正稀缺的仍然是具体的人。
```

## 小红书标题示例

```text
AI真正放大的不是能力
普通人该怎么用AI
为什么AI会放大差距
```

## 注意

如果微信工具链不支持音频插入，播客音频只作为本地播客包产物，不应声称已经嵌入微信草稿。
