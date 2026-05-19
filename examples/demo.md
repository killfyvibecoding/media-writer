# Demo

下面是一个典型任务示例。

## 输入

```text
使用 $media-writer 处理 D:\notes\AI-agent-report.md：
生成播客，并上传微信公众号草稿。
```

## Agent 应执行的流程

1. 读取 `AI-agent-report.md`。
2. 判断用户同时要求播客分支和微信草稿分支。
3. 播客分支：
   - 创建或复用 NotebookLM notebook；
   - 添加 source；
   - 生成 audio overview；
   - 下载音频；
   - 生成标题简介 TXT；
   - 生成播客封面 JPG。
4. 微信草稿分支：
   - 拆解原文结构；
   - 写一篇新的微信文章；
   - 转换为 WeChat HTML；
   - 上传封面；
   - 生成 draft JSON；
   - 创建微信公众平台草稿。

## 示例输出目录

```text
outputs/ai-agent-report/
├── ai-agent-report_podcast.mp3
├── ai-agent-report_podcast_info.txt
├── ai-agent-report_podcast_cover.jpg
├── ai-agent-report_teardown.md
├── ai-agent-report_wechat_rewrite.md
├── ai-agent-report_wechat_rewrite.wechat.html
├── ai-agent-report_wechat_rewrite.image-map.json
├── ai-agent-report_wechat_rewrite.draft.json
└── ai-agent-report_draft_result.json
```

## 播客标题简介示例

```text
标题：
AI会把你放大成谁

简介：
这一期从一篇长文出发，聊 AI 如何放大人的判断、品位、组织能力和信任关系。我们会拆解一人公司、组织中部坍塌，以及为什么智能时代真正稀缺的仍然是具体的人。
```

## 注意

如果微信工具链不支持音频插入，MP3 只作为本地播客包产物，不应声称已经嵌入微信草稿。
