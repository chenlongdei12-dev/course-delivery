# video-chapter-slicer

把长视频按语义切成章节小片 —— 一个可被任意 AI Agent 驱动的视频切片 skill。
macOS 原生 Swift + AVFoundation 实现，**无需 ffmpeg**。

从真实会议复盘流水线（腾讯会议录制 → 逐字稿 → 知识库 → 切片上传）中沉淀的切片核心链路，解耦为通用版。

## 它解决什么问题

录了一小时会议 / 课程 / 直播回放，想切成一个个可独立回看的章节小片：

- ✅ 基于逐字稿时间轴**按语义**切片（不是死板的每 N 分钟一刀）
- ✅ 切点自动吸附静音谷（-60dB 以下持续 ≥1s），不腰斩话音
- ✅ 渲染幂等（断点续跑，已完成的章自动跳过）
- ✅ 自动 QC：时长误差 ≤0.25s、音视频轨齐全、首末帧抽帧留档
- ✅ macOS 原生 AVFoundation，零第三方依赖

## 工作原理（三步）

```
分析 → 切片方案(manifest) → 渲染 + QC
```

1. **分析**：`analyze_video.swift` 提取时长/分辨率/逐秒音量（找静音谷）
2. **方案**：AI agent（或人）按语义划章，写成 `render_manifest.json`（划界三原则见 `references/slicing-methodology.md`）
3. **渲染+QC**：`render_chapters.swift` 切片，`verify_outputs.swift` 自动质检

**设计理念：脚本只做确定性计算（音量分析/渲染/QC），语义判断（哪里切、标题起什么）交给 AI agent。**

## 快速开始

### 环境要求

- macOS 12+
- Swift（系统自带；没有的话终端跑 `xcode-select --install`）

### 纯手动跑一遍

```bash
git clone https://github.com/chenlongdei12-dev/video-chapter-slicer.git
cd video-chapter-slicer

# 1. 分析视频
swift scripts/analyze_video.swift --input /path/your-video.mp4 --output /tmp/analysis
# 查看 /tmp/analysis/metadata.json 和 audio_rms_1s.csv

# 2. 照着 example/render_manifest.example.json 写你自己的 manifest

# 3. 渲染 + QC
swift scripts/render_chapters.swift /path/render_manifest.json
swift scripts/verify_outputs.swift /path/render_manifest.json /path/chapters_qc
# chapters_qc/verification.json 里 failures=0 即全部通过
```

## 安装为 AI Agent 的 Skill

### WorkBuddy

```bash
git clone https://github.com/chenlongdei12-dev/video-chapter-slicer.git ~/.workbuddy/skills/video-chapter-slicer
```

装完后重启会话，对 WorkBuddy 说「把 xx 视频切成片」即可触发。

### Claude Code / 其他 Skill 体系的 Agent

```bash
git clone https://github.com/chenlongdei12-dev/video-chapter-slicer.git ~/.claude/skills/video-chapter-slicer
```

（或放到你的 agent 对应的 skill/指令目录。）

### 没有 skill 体系的 AI Agent（ChatGPT / 任意 CLI agent 等）

把本仓库的 `SKILL.md` 内容作为指令发给你的 agent，agent 按其中「使用流程」执行 swift 命令即可。本质上只需要三个命令：

```bash
swift scripts/analyze_video.swift --input <视频> --output <分析目录>
# agent 写 render_manifest.json
swift scripts/render_chapters.swift <manifest>
swift scripts/verify_outputs.swift <manifest> <qc目录>
```

### 对 AI Agent 说一句话示例

> 帮我把 /Users/me/Videos/meeting.mp4 按内容切成章节小片，我有逐字稿 /Users/me/Videos/meeting.md（带 mm:ss 时间戳），切完自动 QC。

## 划界三原则（摘要）

1. **一个完整知识点 = 一片**：4–15 分钟为宜，任务完整性优先于时长
2. **音画双信号核对**：切点不只看文字边界，还要核对画面与口头主题一致
3. **绝对时间轴**：`in/out` 用源视频绝对秒数，删片头后后续章不平移

完整方法论：[references/slicing-methodology.md](references/slicing-methodology.md)

## 仓库结构

```
video-chapter-slicer/
├── SKILL.md                             # skill 定义（agent 按此执行）
├── README.md
├── scripts/
│   ├── analyze_video.swift              # 元数据 + 逐秒音量（找静音谷）
│   ├── render_chapters.swift            # 按 manifest 渲染章节片
│   └── verify_outputs.swift             # 自动 QC
├── references/
│   └── slicing-methodology.md           # 切片方法论（划界三原则等）
└── example/
    └── render_manifest.example.json     # manifest 示例
```

## 已知限制

- 仅 macOS（AVFoundation）。Windows/Linux 请用 ffmpeg 自行实现等价链路
- 源视频需含音轨（分析依赖音频；无音轨视频可改用纯抽帧方案）
- `passthrough` preset 最快但切点可能漂移到关键帧；对切点精度敏感时用 `1080p` 重编码

## License

MIT
