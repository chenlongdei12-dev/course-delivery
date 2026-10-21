# 阶段 1：腾讯会议导出（逐字稿 + 视频）

## 输入
- 会议号（meeting_code）或「今天的已结束会议」（`tmeet meeting list-ended --start <当天00:00> --end <当天23:59>`）
- tmeet 已登录（阶段 0）

## 流程

### 1.1 查会议与录制状态

```bash
tmeet meeting get --meeting-code "<会议号>" --compact
```

看 `records[]`：
- `permission_status` 必须 `can_view`；`can_apply` 走权限申请（需用户确认后 prepare→commit）
- `state` 必须含「转码完成」；「录制中/转码中」→ 等待，30 分钟后重试（自动化场景最多重试到次日 02:00）
- 两条记录：`type=云录制` 是视频，`type=文字转写` 是逐字稿

### 1.2 导出逐字稿（纯 CLI，无需登录）

逐字稿走 `record address` 拿 view_address 后，用浏览器打开会强制密码；**直接走网页下载**更稳（见 1.3 一并做）。若装了 WorkBuddy ima/tmeet MCP 可用 transcript 接口直取。

纯 CLI 替代（tmeet 支持时优先）：
```bash
tmeet record transcript-get --record-file-id "<records[文字转写].record_file_id>"
```

### 1.3 导出视频 + 逐字稿文件（网页通道，需扫码登录一次）

录制文件的「下载至本地」只在网页端提供，且**播放页密码与入会密码不是一回事**，所以统一走网页登录：

```bash
export PATH="<node_modules>/.bin:$PATH"
playwright-cli open https://meeting.tencent.com/crw/<view_address后缀> --browser=chrome
```

页面流程（Agent 驱动 playwright-cli 完成）：
1. 出现「请输入密码」→ **别试入会密码**（大概率错），点右上「登录」
2. 登录页 → 截图二维码给用户扫码（canvas 元素 `toDataURL` 导出或整页截图）
3. 用户手机确认后可能要求「选择账号」→ 选**个人账号**（录制所有者身份）
4. 回到录制页 → 顶部菜单「另存为」→「下载至本地」
5. 菜单展开后：
   - 点「视频内容」→ 捕获 download 事件 → `dl.saveAs(工作目录/source-video.mp4)`
   - 再「另存为」→「下载至本地」→ 点「逐字稿文本」→ 格式选 **Markdown** → 点「下载」→ `dl.saveAs(工作目录/transcript-raw.md)`

**卡壳点**：
- Playwright 默认内核 crash → 必须 `--browser=chrome`；仍 crash 先 `playwright-cli kill-all`
- 用户 Chrome 正在运行时无法附加 playwright → 用 `open -a "Google Chrome" <url>` 打开让用户手动操作，或让用户先退 Chrome
- 「逐字稿文本」点了没反应是因为它只是格式选项，还要再点「下载」按钮
- 视频文件名含 `-共享屏幕.mp4` 才是屏幕+声音版；下载列表若有多路流，选共享屏幕
- 用户扫码后停在账号选择页，Agent 轮询 URL 变化（离开 qrcode-login.html）判断登录完成

### 1.4 验证产物

- `transcript-raw.md` 非空、含时间戳格式 `(hh:mm:ss)`
- `source-video.mp4` 大小合理（45 分钟课约 100-200MB/1080p）
- md5 记入 manifest.json

完成后更新 manifest：`{"stage1": "done", "transcript": "...", "video": "..."}`
