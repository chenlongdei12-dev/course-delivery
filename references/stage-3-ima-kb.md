# 阶段 3：ima 知识库入库 + 三问三答

## 3.1 逐字稿入库

### 通道 A：WorkBuddy ima 连接器（首选，全自动）

```
mcp__ima-mcp__create_media(content_type="text/markdown", file_ext="md",
    file_name="第N课-<课题>-逐字稿.md", file_size=<实际字节数>, knowledge_base_id=<kb_id>)
→ 拿 cos_credential
→ python3 scripts/ima_upload.py <凭据JSON文件> <本地md>
→ mcp__ima-mcp__add_knowledge(knowledge_base_id, media_id)
```

### 通道 B：无连接器（用 ima 网页版手动/半自动）
用户在 ima 客户端手动上传，或 Agent 驱动浏览器。引导话术：「打开 ima.qq.com → 知识库 → 上传 transcript-checked.md」。

## 3.2 COS 直传脚本

`scripts/ima_upload.py` 已内置实测修复：
- secret_key 用**原始字符串**（勿 base64 解码——44 字符带 `=` 只是巧合）
- FormatString = `put\n/<cos_key>\n\nhost=<bucket>.cos.<region>.myqcloud.com\n`（headers 段末 `\n` 即结束，不补第二个）
- 签名头只签 host；`x-cos-security-token` 必须带

```bash
python3 scripts/ima_upload.py cred.json transcript-checked.md
# HTTP 200 = 成功；403 SignatureDoesNotMatch → 对照上面三条排查
```

## 3.3 三问三答（Agent 的语义工作）

入库后 **等 30-60 秒让 ima 完成解析**（`get_knowledge_list` 看 `media_state=2, parse_progress=100`），然后：

1. Agent 通读校验后逐字稿，提炼 3 个「深刻问题」——标准：
   - 不是事实检索题（「某功能在哪」），而是机制/决策/反直觉洞察题
   - 例：付费机制的底层设计逻辑？产品差异的本质维度？讲师反直觉观点的成本-收益逻辑？
2. 每个问题向 ima 提问（连接器：`search_knowledge(knowledge_base_id, query=<问题全文>)`；无连接器时基于逐字稿自答并标注）
3. 用检索返回的原文片段接地答案，整理成 md（格式：问题为二级标题 + 答案段落，含具体数字与案例）
4. 产物 `三问三答-第N课.md` 存工作目录（阶段 5 会同步到飞书）

## 产物
- ima 知识库新增逐字稿（可被提问）
- `三问三答-第N课.md`
- manifest: `{"stage3": "done", "ima_media_id": "..."}`
