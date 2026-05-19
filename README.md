<div align="center">

# 🎙️ Media Writer

**多源内容智能处理器：任意内容 → NotebookLM 播客包 / 微信公众号草稿**

把文章、剪藏、网页、播客转录稿或长文资料，整理成可交付的播客音频包，并按媒体写作逻辑改写成微信公众号草稿。

![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)
![GitHub stars](https://img.shields.io/github/stars/killfyvibecoding/media-writer?style=social)
![GitHub forks](https://img.shields.io/github/forks/killfyvibecoding/media-writer?style=social)
![GitHub issues](https://img.shields.io/github/issues/killfyvibecoding/media-writer)
![Last Commit](https://img.shields.io/github/last-commit/killfyvibecoding/media-writer)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Made with AI](https://img.shields.io/badge/Made%20with-AI-8A2BE2)

[快速开始](#-快速开始) ·
[支持格式](#-支持格式) ·
[使用示例](#-使用示例) ·
[配置说明](#-配置说明) ·
[常见问题](#-常见问题)

</div>

---

## 📌 项目简介

Media Writer 是一个面向 Codex / Agent 工作流的本地 Skill 仓库。它把两个常见但容易割裂的媒体生产动作拆成两个可独立触发的分支：

- **播客分支**：读取任意可用资料，上传或添加到 NotebookLM，生成中文播客音频，并产出标题、简介和封面。
- **微信公众号草稿分支**：读取原始内容，先做结构分析和选题拆解，再改写为新的中文公众号文章，转换为 WeChat HTML，上传封面并创建微信公众平台草稿。

这不是一个“把原文复制到公众号”的脚本，而是一个用于内容再创作、媒体包装和多渠道交付的 Agent Skill。

## 🤔 为什么需要这个项目

内容创作者经常会遇到三个问题：

1. 好内容分散在 Markdown、网页、X/Twitter、播客转录稿和笔记工具里。
2. 播客生成、封面制作、标题简介、公众号排版和草稿上传分别依赖不同工具。
3. 直接转换会保留太多原文痕迹，不适合公众号这类需要重新开题、重写开头和重构节奏的平台。

Media Writer 的目标是把这些步骤组织成一个稳定流程：**先理解内容，再按媒体平台重新写作，最后产出可以直接检查和发布的交付物**。

## ✨ 核心功能

1. **NotebookLM 播客生成**：创建或复用 NotebookLM 笔记本，添加 source，生成 audio overview，并下载音频。
2. **播客包装**：生成播客标题、简介和 16:9 封面图。
3. **媒体写作分析**：拆解原文标题、开头、结构、受众、承诺、案例和可复用洞察。
4. **公众号重写**：基于原始内容重构角度、结构、语气和标题，生成新的微信长文。
5. **微信草稿上传**：转换 Markdown 为 WeChat HTML，处理图片和封面，调用 `md2wechat` 创建微信公众号草稿。

## 📚 支持格式

| 输入类型 | 当前支持方式 |
| --- | --- |
| Markdown / TXT | 直接读取并作为 NotebookLM source 或公众号改写源 |
| 微信公众号文章 | 抓取为可读文本后处理 |
| 普通网页 / 博客 / Newsletter | 优先直接添加 URL；必要时抓取正文 |
| X / Twitter 链接 | 优先直接处理；受限时转为 Markdown/TXT |
| YouTube URL | 推荐直接添加到 NotebookLM |
| 小宇宙 / 喜马拉雅 / Bilibili | 需要转录稿时使用脚本提取或外部转录 |
| PDF / DOCX / PPTX / EPUB | 先转换为 Markdown/TXT 后处理 |

更多细节见 [docs/supported-formats.md](docs/supported-formats.md)。

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/killfyvibecoding/media-writer.git
cd media-writer
```

### 2. 安装 Python 依赖

```bash
python -m pip install -r requirements.txt
```

### 3. 安装为本地 Codex Skill

Windows PowerShell 示例：

```powershell
$SkillRoot = "$env:USERPROFILE\.codex\skills\media-writer"
New-Item -ItemType Directory -Force -Path $SkillRoot
Copy-Item -Path ".\*" -Destination $SkillRoot -Recurse -Force
```

安装后，在 Codex 中可以这样触发：

```text
使用 $media-writer 处理这篇 Markdown：生成播客，并上传微信公众号草稿。
```

## ⚙️ 安装方式

Media Writer 本身主要由 Skill 指令、Python 脚本和 PowerShell 辅助脚本组成。真实运行还需要你本机配置好外部工具。

### 必需

- Python 3.9+
- `Pillow`，用于本地生成播客封面
- Codex 本地 Skills 目录，或兼容 `SKILL.md` 的 Agent 环境

### 按需配置

- NotebookLM CLI：用于创建 NotebookLM source、生成和下载音频
- `md2wechat` CLI：用于 Markdown 转 WeChat HTML、图片上传和草稿创建
- 微信公众平台 AppID / Secret，并将当前机器 IP 加入微信后台白名单

> 密钥、Cookie、`md2wechat.yaml`、`.env` 等文件不要提交到仓库。

## 🧪 使用示例

### 只生成播客

```text
使用 $media-writer 处理 ./notes/source.md，生成播客音频、标题简介和播客封面。
```

预期产物：

- `*_podcast.mp3`
- `*_podcast_info.txt`
- `*_podcast_cover.jpg`

### 只生成微信公众号草稿

```text
使用 $media-writer 读取这篇文章，先分析和改写，再上传到微信公众号草稿。
```

预期流程：

1. 读取或抓取 source
2. 分析原文结构和可复用洞察
3. 写成新的微信文章
4. 转换为 WeChat HTML
5. 上传封面
6. 创建公众号草稿

### 同时生成播客和微信草稿

```text
使用 $media-writer 处理 D:\notes\article.md：生成播客，并上传微信公众号草稿。
```

该请求会同时触发两个分支，但播客音频不会被自动塞进微信草稿，除非你当前的 `md2wechat` 能力明确支持音频素材插入。

更多示例见 [examples/demo.md](examples/demo.md)。

## 🔧 配置说明

### NotebookLM

请先在本机完成 NotebookLM CLI 登录，并通过 CLI 的 `--help` 输出确认可用命令。Skill 会以 live CLI 能力为准，不假设不同版本 CLI 的参数完全相同。

### md2wechat

`md2wechat` 需要在本机保存配置，例如：

```yaml
wechat_appid: "your_appid"
wechat_secret: "your_secret"
default_convert_mode: "api"
default_theme: "default"
```

配置文件不要提交。更多命令见 [references/wechat-flow.md](references/wechat-flow.md)。

## 🧱 项目结构

```text
media-writer/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── scripts/
│   ├── build_podcast_wechat_markdown.py
│   ├── fetch_url.sh
│   ├── get_podcast_transcript.py
│   ├── make_podcast_cover.py
│   ├── make_podcast_info.py
│   ├── make_wechat_draft_json.py
│   ├── New-LocalWechatCover.ps1
│   └── publish_markdown_to_wechat.py
├── references/
│   ├── notebooklm-podcast-flow.md
│   └── wechat-flow.md
├── docs/
│   ├── quick-start.md
│   ├── faq.md
│   └── supported-formats.md
├── examples/
│   └── demo.md
├── assets/
│   ├── demo.png
│   └── .gitkeep
└── .github/
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md
    │   └── feature_request.md
    └── pull_request_template.md
```

## 🧭 常见使用场景

- 把一篇长文做成 NotebookLM 中文播客。
- 把 Obsidian / Markdown 剪藏改写成公众号文章草稿。
- 把播客转录稿二次创作为公众号长文。
- 给自媒体选题生成标题、简介、封面和可审稿件。
- 为知识博主建立“资料 → 音频 → 微信草稿”的半自动工作流。

## 🖼️ 截图 / Demo 预览

> 将你的运行截图放到 `assets/demo.png` 后，可以在这里展示。

![Demo Preview](assets/demo.png)

## 🗺️ Roadmap

- [ ] 增加跨平台安装脚本。
- [ ] 增加示例输出包。
- [ ] 增加更完整的 NotebookLM CLI 版本兼容表。
- [ ] 在 `md2wechat` 支持音频素材插入后，补齐公众号音频嵌入流程。
- [ ] 增加 Web UI 或 TUI 任务面板。
- [ ] 增加 Docker 运行示例。

## ❓ 常见问题

### 生成播客会自动上传微信公众号草稿吗？

不会。播客分支和微信草稿分支是两个独立层面。只有当你明确说“生成播客，并上传微信公众号草稿”时，才会同时运行两个分支。

### 微信草稿里会自动包含 MP3 吗？

默认不会。当前稳定流程是生成本地 MP3，同时创建微信文章草稿。只有当你本机 `md2wechat capabilities --json` 明确显示支持音频/voice 素材上传和插入时，才应继续做音频嵌入。

### 为什么需要先分析再改写？

因为公众号草稿不是简单格式转换。Skill 会先拆解原文的结构和洞察，再重构角度、标题、开头、段落节奏和结尾，避免轻微改写或复制原文。

更多问题见 [docs/faq.md](docs/faq.md)。

## 🤝 贡献指南

欢迎提交 Issue 和 PR。建议优先贡献：

- 新输入格式的处理经验；
- NotebookLM CLI 不同版本的兼容参数；
- `md2wechat` 错误码和解决方案；
- 更好的封面模板；
- 更清晰的文档和示例。

提交 PR 前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## ⭐ Star History

如果这个项目帮你把一次内容生产流程跑通，欢迎给一个 Star。它能帮助后来者判断这个 Skill 是否值得尝试。

[![Star History Chart](https://api.star-history.com/svg?repos=killfyvibecoding/media-writer&type=Date)](https://star-history.com/#killfyvibecoding/media-writer&Date)

## 📄 License

本项目基于 [MIT License](LICENSE) 开源。

## 🙏 作者 / 致谢

作者：killfyvibecoding

感谢 NotebookLM、md2wechat 以及所有把内容工作流自动化的人。本项目也继承了两个方向的实践经验：NotebookLM 内容生成流程和 media-transfer 式微信公众号草稿生产流程。
