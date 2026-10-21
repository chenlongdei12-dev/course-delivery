# 阶段 4：视频语义切片（内嵌 video-chapter-slicer）

本阶段完全复用 `vendor/video-chapter-slicer/`（已整合进本仓库，无需单独安装）。其 SKILL.md 是完整文档，这里只写本流水线视角的要点。

## 前置
- macOS 12+、Swift（`swift --version` 验证）
- `transcript-checked.md`（用校验稿切片，标题更干净）
- `source-video.mp4`

## 流程（在 vendor/video-chapter-slicer 目录执行）

```bash
cd <skill>/vendor/video-chapter-slicer

# 1. 分析（拿时长/分辨率/逐秒音量）
swift scripts/analyze_video.swift --input <工作目录>/source-video.mp4 --output <工作目录>/analysis

# 2. Agent 定方案：通读逐字稿 → 语义聚合章节（4-15 分钟/章）→ 写 render_manifest.json
#    切点吸附音量谷：本流水线提供辅助脚本
python3 <skill>/scripts/find_cut_points.py <工作目录>/analysis/audio_rms_1s.csv <候选切点秒数...>

# 3. 渲染（幂等，1080p）
swift scripts/render_chapters.swift <工作目录>/render_manifest.json

# 4. QC（failures=0 才算过）
swift scripts/verify_outputs.swift <工作目录>/render_manifest.json <工作目录>/chapters_qc
```

## 本流水线实测经验（已固化进脚本）

- **腾讯会议录音底噪高于 -60dB，几乎没有绝对静音谷**——`find_cut_points.py` 已实现「±15s 窗口相对低谷」算法，直接给出吸附后切点
- 69 分钟视频 1080p 渲染约 10 分钟（M1 级 Mac）
- QC 检查时长误差 ≤0.25s、音视频轨、首末帧——`failures=0` 后才可进入阶段 5

## 章节命名规范（供 Agent 起标题）

`NN_章节标题.mp4`（NN=两位序号）；标题避免 `/ \ : * ? " < > |`，中文可用。飞书嵌入时文件名改为 `N.M_标题.mp4` 格式（N=课次，M=章节序）。

## 产物
- `chapters/*.mp4`、`render_manifest.json`、`切分方案.md`、`chapters_qc/verification.json`
- manifest: `{"stage4": "done", "chapters": 9, "qc_failures": 0}`
