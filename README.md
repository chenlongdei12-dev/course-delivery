# course-delivery

**课程课后全自动交付流水线** —— 直播课讲完，学员自动拿到：飞书交付文档（含章节切片视频卡片 + 三问三答）+ ima 知识库逐字稿 + 百度/夸克网盘备份分享。

设计为 **AI Agent 驱动**：脚本做确定性工作（导出/切片/上传），语义判断（章节划分、深刻提问、文档填充）交给 Agent。任何 Agent（Claude Code / Codex / WorkBuddy / 任意 CLI Agent）拿到本仓库即可运行。

## 流水线

```
[1] 腾讯会议导出      逐字稿 md + 共享屏幕版视频 mp4（tmeet CLI + 网页通道）
[2] 逐字稿校验        品牌名/错别字/口语规整 + 自动质检脚本
[3] ima 知识库        逐字稿入库（COS 直传协议）+ Agent 三问三答
[4] 视频语义切片      内嵌 video-chapter-slicer（Swift/AVFoundation，无需 ffmpeg）
[5] 飞书交付文档      模板复制 → 填充 → 视频卡片嵌入（lark-cli）
[6] 网盘备份          百度网盘(bdpan) + 夸克网盘(自研分片上传器) + 分享链接
```

每个阶段幂等，manifest 断点续跑；首次运行的所有卡壳点已写入 [SKILL.md](SKILL.md) 速查表。

## 快速开始

```bash
git clone https://github.com/chenlongdei12-dev/course-delivery.git ~/.workbuddy/skills/course-delivery
python3 ~/.workbuddy/skills/course-delivery/scripts/preflight.py   # 环境自检
```

然后对 Agent 说：「按 course-delivery 流程处理今天的课程交付，会议号 xxx」。

配置、定时自动化（每晚 23:00）、各阶段细节见 [SKILL.md](SKILL.md) 与 [references/](references/)。

## 仓库结构

```
SKILL.md                    主编排（Agent 入口）
references/stage-{0..6}*.md 各阶段操作文档（含踩坑解法）
scripts/                    preflight / manifest / 逐字稿质检 / 切点吸附 /
                            ima COS 上传 / 夸克 Cookie 解密 / 夸克分片上传 / 夸克 CLI
vendor/video-chapter-slicer 视频切片子 Skill（独立可用）
example/course.example.json 课程配置示例
```

## License

MIT
