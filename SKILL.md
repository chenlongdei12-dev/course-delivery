---
name: course-delivery
description: 课程课后全自动交付流水线。每晚课程结束后（如 23:00），自动从腾讯会议导出逐字稿与录制视频 → 校验逐字稿 → 上传 ima 知识库并向其提 3 个深刻问题 → 视频按语义切片（内嵌 video-chapter-slicer）→ 上传飞书交付文档（按模板嵌入视频卡片）→ 备份百度网盘与夸克网盘并生成分享链接。当用户要求「跑课程交付」「课后自动交付」「导出课程视频与逐字稿」「搭建课后自动化」时使用。
version: 1.0.0
license: MIT
---

# 课程课后交付流水线（course-delivery）

一门直播课讲完 → 学员拿到「飞书交付文档 + ima 知识库 + 网盘备份」的完整交付物。本 Skill 把这条流水线标准化，任何 AI Agent（Claude Code / Codex / WorkBuddy / 任意 CLI Agent）拿到本仓库即可驱动。

## 流水线总览（7 个阶段）

```
[0] 配置（首次） → [1] 腾讯会议导出 → [2] 逐字稿校验 → [3] ima 知识库入库+三问三答
                   → [4] 视频语义切片 → [5] 飞书交付文档 → [6] 网盘备份+分享
```

**每个阶段都是幂等的**：已完成的产物会跳过，断点续跑。阶段产物统一落在一个工作目录（默认 `~/Desktop/<课程名>/`），目录内 manifest 记录进度。

**AI Agent 的职责**：本 Skill 的脚本只做确定性工作（下载/上传/切片/校验），语义判断（章节划分、三问三答、飞书文档填充）由 Agent 完成。各阶段文档写明了 Agent 应该怎么做。

## 快速开始

```bash
git clone https://github.com/chenlongdei12-dev/course-delivery.git ~/.workbuddy/skills/course-delivery
# 或任意 Agent 的 skills 目录 / 任意目录（把 SKILL.md 内容发给 Agent 亦可）
```

对 Agent 说：**「按 course-delivery 流程，处理今天的课程交付」** 即可启动。

## 阶段详解（Agent 按需读对应 references/*.md，不要一次全读）

| 阶段 | 文档 | 干什么 | 前置条件 |
|------|------|--------|----------|
| 0 配置 | [stage-0-setup.md](references/stage-0-setup.md) | 环境自检、账号授权、课程配置文件 | 无 |
| 1 腾讯会议导出 | [stage-1-tmeet-export.md](references/stage-1-tmeet-export.md) | tmeet CLI 导出逐字稿(md) + 共享屏幕版视频(mp4) | tmeet 登录；录制转码完成 |
| 2 逐字稿校验 | [stage-2-transcript-check.md](references/stage-2-transcript-check.md) | 按校验提示词核对逐字稿（口语转书面、错别字、术语） | 校验提示词模板 |
| 3 ima 知识库 | [stage-3-ima-kb.md](references/stage-3-ima-kb.md) | 逐字稿入库 + Agent 向 ima 提出 3 个深刻问题并整理答案 | ima MCP 连接器 / Cookie |
| 4 视频切片 | [stage-4-slice.md](references/stage-4-slice.md) | 内嵌 video-chapter-slicer：分析→方案→渲染→QC | macOS Swift；逐字稿 |
| 5 飞书交付文档 | [stage-5-feishu-doc.md](references/stage-5-feishu-doc.md) | 按模板复制文档→填课程表→嵌视频卡片→三问三答 | lark-cli 登录 |
| 6 网盘备份 | [stage-6-cloud-backup.md](references/stage-6-cloud-backup.md) | 百度网盘(bdpan) + 夸克网盘(自研上传器) 上传+分享 | bdpan 登录；夸克 Cookie |

## 工作目录约定

```
~/Desktop/<课程文件夹>/            ← 一节课一个目录
├── manifest.json                 ← 进度清单（脚本自动维护）
├── transcript-raw.md             ← 阶段1产物：原始逐字稿
├── transcript-checked.md         ← 阶段2产物：校验后逐字稿
├── source-video.mp4              ← 阶段1产物：完整视频
├── analysis/                     ← 阶段4产物：音量分析
├── chapters/                     ← 阶段4产物：切片视频
├── render_manifest.json          ← 阶段4产物：切片方案
└── 切分方案.md                   ← 阶段4产物：人读版方案
```

## 定时自动化（可选）

用户说「每晚 23:00 自动跑」时，用宿主 Agent 的定时任务能力（如 WorkBuddy automation、cron + agent CLI）调度：
- **prompt 写成自包含**：课程名、会议号、输出目录、各账号状态——定时运行的 Agent 没有本次对话上下文
- 23:00 启动通常已满足「录制转码完成」（课程 21:00 结束，转码一般 <1h）；若未转码完，脚本会报告并等待，Agent 应安排 30 分钟后重试
- **多章方案无人值守**：自动渲染但报告标注「方案未经人工确认，建议次日复核切点」

## 卡壳点速查（实测踩坑，全部来自首次运行）

<details>
<summary>点开看全部（Agent 遇错先查这里）</summary>

1. **tmeet 播放页密码 ≠ 入会密码**——下载录制需网页登录（扫码+选个人账号），不能用入会密码
2. **Playwright 默认内核 Target crashed**——用 `--browser=chrome` 且先 `kill-all`；Chrome 主进程已运行时无法附加，退回 `open -a "Google Chrome"` 让用户手动操作
3. **Chrome Cookie 解密**——v10 格式 = PBKDF2(Keychain "Chrome Safe Storage", saltysalt, 1003, 16B) AES-CBC；新版有 32 字节 hash 前缀要剥掉
4. **ima COS 上传**——secret_key 直接用原始字符串（不要 base64 解码）；FormatString 末尾 headers 段的 `\n` 后不再补 `\n`
5. **夸克上传**——auth 接口返回字段是 `auth_key`（不是 sign）；分片 ETag 用 PUT 响应头（不是本地 md5）；pre 是单文件字段格式
6. **lark-cli 路径白名单**——只允许 cwd / /tmp / ~/files；其他路径先 `cp` 到 /tmp
7. **lark-cli block 操作**——跨容器范围 replace/delete 报 1002，必须逐顶层块操作
8. **GitHub 直连超时**——用 `https://gh-proxy.com/<完整URL>` 克隆
9. **视频下载选「共享屏幕」版**——文件名含 `-共享屏幕.mp4` 的才是屏幕+声音版
10. **分享有效期没有 365 天**——百度/夸克都只有 永久/1/7/30，按永久设置并告知用户

</details>

## 红线

- 永不改动源视频与原始逐字稿（校验产物另存）
- 分享链接一旦生成即视为公开，涉密内容分发前必须用户确认
- 各账号凭据（Cookie/Token）永不写入仓库、日志、文档
- QC 不过的切片不进入交付文档
