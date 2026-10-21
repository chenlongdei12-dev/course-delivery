# 阶段 5：飞书交付文档

## 5.1 从模板创建文档

```bash
lark-cli drive +copy --url "<course.json 的 feishu_template_url>" \
  --name "<课程名>交付文档（第X期）" --folder-token my_space
```

记录新文档 token（URL 中 `/docx/` 后那段）。

## 5.2 填充顺序（实测最优，减少 block id 失效）

1. **读结构**：`lark-cli docs +fetch --doc <token> --scope outline --max-depth 3 --detail with-ids`
2. **填头部**：课程定位 callout（block_replace 整个 callout）、配套知识库链接、三件套、课程表（整表 block_replace）
3. **填本课模块 vol.N**：标题 str_replace → 学习目标 callout → 信息卡 table → 小节清单 li
4. **嵌视频卡片**（见 5.3）
5. **文末追加三问三答**：`--command append`，导语注明「由 Agent 调用 ima 知识库提问整理」
6. **删模板占位**：使用说明框、vol.0N 示例模块、未用的行——**逐顶层块 block_delete**（跨容器范围删除会报 1002）
7. **终检**：fetch markdown 全文，正则查占位残留（`本课主题|M 月 D 日|目标一|vol\.0N` 等）应为 0

## 5.3 视频上传与嵌入

**上传**（注意路径白名单：cwd / /tmp / ~/files）：

```bash
# 工作目录的文件先复制到 /tmp
cp "<工作目录>/chapters/01_xxx.mp4" /tmp/upload/ && cd /tmp/upload
lark-cli drive +upload --file 01_xxx.mp4
# 记录返回 file_token；逐个上传全部切片 + 大课完整版
```

**嵌入**（vol.N 模块「正式开讲」下方，替换原占位行）：

```xml
<figure view-type="Card"><source token="<file_token>" name="N.01_标题.mp4"/></figure>
...（每个切片一个 figure）
<p><b>大课完整版：</b></p>
<figure view-type="Preview"><source token="<token>" name="N. 课题-大课完整版.mp4"/></figure>
<p>腾讯会议纪要版（未剪辑）：<会议回放url></p>
```

一次 block_replace 写入全部 figure（内容是同父连续层级，实测可行）。

## 5.4 配套知识库链接

「配套知识库 · 入口链接」填 course.json 的 `ima_kb_share_url`（ima 知识库分享链）。

## 卡壳点
- callout 内不能放 table/figure；嵌套内容放 callout 外
- 每次写操作后 block id 变化，重 fetch 再定位
- 视频上传大文件慢（200MB 约 1 分钟），串行即可，别并发

## 产物
- 飞书文档 URL
- manifest: `{"stage5": "done", "doc_url": "..."}`
