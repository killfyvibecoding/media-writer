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

### md2wechat

确认本机可运行 md2wechat：

```bash
md2wechat version --json
md2wechat capabilities --json
md2wechat config validate
```

如果你使用的是本地可执行文件，请在实际任务中提供它的路径，或把它加入 PATH。

## 5. 触发 Skill

只生成播客：

```text
使用 $media-writer 处理 ./article.md，生成播客音频、标题简介和封面。
```

只生成微信草稿：

```text
使用 $media-writer 处理 ./article.md，分析改写后上传微信公众号草稿。
```

同时运行两个分支：

```text
使用 $media-writer 处理 ./article.md，生成播客，并上传微信公众号草稿。
```

## 输出物

常见输出包括：

- `*_podcast.mp3`
- `*_podcast_info.txt`
- `*_podcast_cover.jpg`
- `*_wechat_rewrite.md`
- `*.wechat.html`
- `*.draft.json`
- `*_draft_result.json`
