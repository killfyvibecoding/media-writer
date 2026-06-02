# Quick Start

这份文档给出最短可运行路径。完整背景请看根目录 [README.md](../README.md)。

## 1. 克隆项目

```bash
git clone https://github.com/killfyvibecoding/media-writer.git
cd media-writer
```

## 2. 安装依赖

```bash
python -m pip install -r requirements.txt
```

## 3. 安装为 Codex Skill

Windows PowerShell：

```powershell
$SkillRoot = "$env:USERPROFILE\.codex\skills\media-writer"
New-Item -ItemType Directory -Force -Path $SkillRoot
Copy-Item -Path ".\*" -Destination $SkillRoot -Recurse -Force
```

macOS / Linux：

```bash
mkdir -p "$HOME/.codex/skills/media-writer"
cp -R ./* "$HOME/.codex/skills/media-writer/"
```

## 4. 准备外部工具

### NotebookLM

确认本机可运行 NotebookLM CLI：

```bash
notebooklm --help
```

如果需要登录，请按 CLI 提示完成浏览器登录。

### HyperFrames

确认本机可运行 HyperFrames：

```bash
node --version
npx hyperframes info
npx hyperframes doctor
```

PPT+播客视频分支默认使用 HyperFrames 渲染最终 MP4，不静默降级为 ffmpeg。

### md2wechat

确认本机可运行 md2wechat：

```bash
md2wechat version --json
md2wechat capabilities --json
md2wechat config validate
```

如果你的安装只显示 `--markdown`、`--html`、`--cover`、`--title` 等参数，说明它是 direct-publish 模式，也可以使用。实际任务中提供可执行文件路径，或把它加入 PATH。

## 5. 触发 Skill

可读取源内容时，Skill 会先生成内容诊断文件，再运行播客、PPT、微信草稿或小红书分支。

只生成播客：

```text
使用 $media-writer 处理 ./article.md，生成播客音频、标题简介和封面。
```

只生成 PPT：

```text
使用 $media-writer 处理 ./article.md，生成 PPT。先输出按页的理解与决策结果、中文版提示词和英文版提示词，再生成可视化幻灯片。
```

只生成微信草稿：

```text
使用 $media-writer 处理 ./article.md，分析改写后上传微信公众号草稿。
```

只生成小红书科普帖：

```text
使用 $media-writer 处理 ./article.md，生成小红书科普帖和热门相关标签。
```

生成 PPT+播客动态视频：

```text
使用 $media-writer 处理 ./article.md，生成 PPT、播客，并把 PPT 和播客合成动态视频。
```

使用已有 PPT 和播客：

```text
使用 $media-writer 把 ./deck.pptx 和 ./podcast.m4a 合成 16:9 动态视频。
```

同时运行多个分支：

```text
使用 $media-writer 处理 ./article.md，生成播客、微信公众号草稿和小红书科普帖。
```

## 输出物

常见输出包括：

- `*_content_diagnosis.md`
- `*_content_diagnosis.json`
- `*_podcast.m4a`
- `*_podcast_info.txt`
- `*_podcast_cover.jpg`
- `*_ppt_design_prompts.md`
- `*_slides_artifact.txt` 或 `*.pptx`
- `*_video.mp4`
- `*_video_manifest.json`
- `*_video_project/`
- `*_slides/`
- `*_wechat_rewrite.md`
- `*.wechat.html`
- `*.draft.json`
- `*_draft_result.json`
- `*_xiaohongshu_post.md`
- `*_xiaohongshu_post.json`
