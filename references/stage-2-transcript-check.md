# 阶段 2：逐字稿校验

## 输入
`transcript-raw.md`（腾讯会议导出的原始转写）

## 校验提示词模板

Agent 用以下提示词对逐字稿做一轮校对（在对话中直接处理，产出 `transcript-checked.md`）：

```
你是课程逐字稿校对员。对下面的课程逐字稿执行校验，规则：

1. 保留说话人(hh:mm:ss)时间戳结构，不改时间、不删段落、不调顺序
2. 修正语音识别错误：
   - 品牌名/产品名规范：workbody→WorkBuddy、open cloud/opencloud→OpenClaude、cloud code→Claude Code、质谱/质朴→智谱、deep sync→DeepSeek、混元 hy4→混元 h4
   - 明显错别字与同音字（的地得不做强制）
   - 口语重复词（"然后然后"）压成单个，语气词（嗯、啊、呃）单独成句时删除
3. 数字与单位规范化：4000个积分、19:30、5小时
4. 不确定的识别结果用【？】标注，不要猜
5. 输出完整校对稿，不要省略段落

逐字稿：
<贴入 transcript-raw.md 全文>
```

> **用户可自定义**：把自定义校验提示词存为工作目录 `check-prompt.md`，Agent 优先用它。

## 自动质检（脚本）

```bash
python3 scripts/check_transcript.py <工作目录>/transcript-checked.md
```

检查项：时间戳单调递增、说话人标注齐全、占位符【？】数量（>20 提示人工复核）、段落完整率。

## 产物
- `transcript-checked.md`
- manifest: `{"stage2": "done", "question_marks": N}`
