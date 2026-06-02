## 变更概述

请说明这次 PR 改了什么。

## 变更原因

为什么需要这次改动？

## 验证方式

- [ ] `python -m py_compile scripts/*.py`
- [ ] `python tests/test_make_content_diagnosis.py -v`
- [ ] `python tests/test_make_xiaohongshu_post.py -v`
- [ ] `python tests/test_run_notebooklm_podcast.py -v`
- [ ] `python tests/test_run_notebooklm_artifact.py -v`
- [ ] `python tests/test_run_ppt_podcast_video.py -v`
- [ ] 手动验证需要真实外部账号/API的分支，并记录结果
- [ ] 文档链接和命令已检查

## 影响范围

- [ ] SKILL.md 触发逻辑
- [ ] 内容诊断层
- [ ] NotebookLM 流程
- [ ] PPT / 思维导图 / artifact 流程
- [ ] PPT+播客视频流程
- [ ] 微信草稿流程
- [ ] 小红书流程
- [ ] 文档 / 示例
- [ ] 其他：

## 安全检查

- [ ] 没有提交 AppID、Secret、Cookie、token 或本地配置文件
- [ ] 没有承诺尚未实现的功能
- [ ] 没有引入不必要的外部依赖
- [ ] 没有把 NotebookLM runtime/log/state 文件放进用户交付目录或仓库
