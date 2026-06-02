# Supported Formats

Media Writer 的输入处理原则是：**能直接读取就直接读取；不能直接读取就先转成 Markdown/TXT；可读源内容先进入内容诊断，再进入播客、PPT、思维导图、微信草稿或小红书分支**。

## 输入支持

| 格式 / 来源 | 推荐路径 | 说明 |
| --- | --- | --- |
| Markdown `.md` / TXT `.txt` | 直接读取 | 最推荐格式，适合文章、剪藏、转录稿和研究笔记 |
| 微信公众号文章 | 抓取或导出正文 | 可进入诊断、微信改写、播客和小红书分支 |
| 普通网页 / 博客 / Newsletter | 优先 URL，失败时抓正文 | NotebookLM 可直接 ingest 的链接优先直接添加 |
| X / Twitter | 优先已有 Markdown 或可读导出 | 受登录和反爬限制影响时，先转为 Markdown/TXT |
| YouTube URL | NotebookLM 直接添加 | 生成播客或 study artifact 时不要先下载字幕，除非需要转文本给微信 |
| 小宇宙 / 喜马拉雅 / Bilibili | 需要转录稿时先提取 | 可使用 `scripts/get_podcast_transcript.py` 或外部转录 |
| PDF / DOCX / PPTX / EPUB | 先提取正文或转 Markdown | NotebookLM CLI 支持时可直接添加，否则转文本 |
| 多文件 / 多链接 | 重复添加 source | 用同一个 notebook 和同一份诊断策略组织输出 |

## 输出支持

| 输出 | 典型文件 |
| --- | --- |
| 内容诊断 | `*_content_diagnosis.md`, `*_content_diagnosis.json` |
| 播客包 | `*.m4a`, `*_podcast_info.txt`, `*_podcast_cover.jpg` |
| PPT / 幻灯片 | `*_ppt_design_prompts.md`, NotebookLM artifact 记录，或渲染后的 `.pptx` |
| 思维导图 | NotebookLM mind map 记录，或渲染后的 `.png` / `.svg` |
| PPT+播客视频 | `*_video.mp4`, `*_video_manifest.json`, `*_video_project/`, `*_slides/` |
| 微信公众号草稿 | `*_wechat_rewrite.md`, `*.wechat.html`, `*.draft.json`, `*_draft_result.json` |
| 小红书科普帖 | `*_xiaohongshu_post.md`, `*_xiaohongshu_post.json` |

## 不承诺的能力

- 绕过付费墙、登录墙或权限限制。
- 在未验证 `md2wechat` 能力前，声称音频已嵌入微信草稿。
- 在没有真实平台研究时，声称小红书标签是实时热榜。
- 在 NotebookLM CLI 没有导出能力时，虚构本地 PPTX/PDF 文件。
- 对所有网页进行 100% 成功抓取。

## 关键约束

- 播客默认交付 `.m4a`，不要把它改名成 `.mp3`，除非真实转码生成了 MP3。
- PPT 和思维导图不能只交付 Markdown；用户期望可视结果时必须交付 `.pptx`、`.png`、`.svg` 或可验证的 NotebookLM artifact。
- 长任务优先 CLI/后台运行，浏览器只用于一次性登录或 CLI 失败后的最后 fallback。
