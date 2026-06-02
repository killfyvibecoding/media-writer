# Contributing

感谢你愿意改进 Media Writer。这个项目的目标是让内容生产流程更稳定，而不是把所有功能塞进一个不可维护的大脚本。

## 可以贡献什么

- 新输入格式的处理说明或脚本。
- NotebookLM CLI 参数兼容经验。
- md2wechat 错误码、配置问题和修复方案。
- 内容诊断、PPT/思维导图、小红书和视频分支的真实案例。
- 更稳的 Markdown 转微信 HTML 流程。
- 更好的封面生成模板。
- 文档、示例和 FAQ 改进。

## 开发流程

1. Fork 仓库。
2. 创建分支：

```bash
git checkout -b feature/your-change
```

3. 安装依赖：

```bash
python -m pip install -r requirements.txt
```

4. 修改文件并运行基础检查：

```bash
python -m py_compile scripts/*.py
python tests/test_make_content_diagnosis.py -v
python tests/test_make_xiaohongshu_post.py -v
python tests/test_run_notebooklm_podcast.py -v
python tests/test_run_notebooklm_artifact.py -v
python tests/test_run_ppt_podcast_video.py -v
```

5. 提交 PR，并说明：

- 改了什么；
- 为什么需要；
- 如何验证；
- 是否影响已有 Skill 触发逻辑。

## 文档原则

- 不要承诺尚未实现的功能。
- 涉及密钥、Cookie、token 的内容只能写配置方式，不要提交真实值。
- README 面向使用者，`SKILL.md` 面向 Agent，二者不要互相堆叠。

## 代码风格

- Python 脚本优先使用标准库。
- 只在确实需要时引入第三方依赖。
- 保持命令可复制。
- 对长流程保留可恢复的中间 ID 或结果文件。

## 提交信息

建议使用简短的祈使句：

```text
Add NotebookLM retry notes
Fix WeChat draft JSON metadata
Document supported source formats
Update diagnosis-driven podcast flow
```
