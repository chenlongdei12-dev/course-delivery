# 阶段 0：环境配置（首次运行）

Agent 引导用户完成一次，之后每节课免配置。

## 1. 环境自检

跑自检脚本，缺什么补什么：

```bash
python3 scripts/preflight.py
```

输出每项 `✓/✗`。✗ 项按下表处理：

| 依赖 | 安装方式 | 备注 |
|------|----------|------|
| macOS 12+ + Swift | `xcode-select --install` | 仅视频切片需要 |
| Node 18+ | 官网/pkg | playwright-cli 需要 |
| tmeet CLI | `npm install -g @tencentcloud/tmeet@latest` | 腾讯会议导出 |
| lark-cli | 飞书连接器自带；独立装见 lark 官方文档 | 飞书文档 |
| bdpan CLI | `bash <skill目录>/scripts/install-bdpan.sh`（用户确认后） | 百度网盘 |
| Python 3.9+ | 系统自带 | 上传器 |

## 2. 账号授权（每账号一次）

| 账号 | 授权方式 | 验证命令 |
|------|----------|----------|
| 腾讯会议 | `tmeet auth login`（阻塞式，输出 URL 后等浏览器 OAuth，**必须前台**） | `tmeet auth status` |
| 飞书 | lark-cli 首次使用时引导 OAuth | `lark-cli auth status` |
| 百度网盘 | `bash scripts/bdpan-login.sh`（引导扫码） | `bdpan whoami` |
| 夸克网盘 | `python3 scripts/quark_cookie.py --check`（自动开浏览器检测/等待扫码） | 同左返回容量 |
| ima | 走 WorkBuddy ima 连接器（MCP）；无连接器时 Agent 用 ima 网页（需用户登录） | `mcp__ima-mcp__get_knowledge_base_list` |

**卡壳点**：
- tmeet login 是阻塞命令，别放后台；无默认浏览器环境只给用户 URL 让其手动开
- Chrome Cookie 解密需要 Keychain 访问权限，首次会弹窗要求授权「安全与隐私」，引导用户点允许

## 3. 课程配置文件

每期课程一份 `course.json`（放 Skill 目录或工作目录均可）：

```json
{
  "course_name": "WorkBuddy AI 办公自动化实操营",
  "teacher": "陈龙得",
  "workdir_template": "~/Desktop/workbuddy 实训营",
  "feishu_template_url": "https://my.feishu.cn/docx/xxxx",
  "ima_kb_id": "7518578462953247",
  "ima_kb_share_url": "https://ima.qq.com/wiki/?shareId=xxxx",
  "baidu_remote_dir": "workbuddy实训营",
  "quark_dir_name": "workbuddy实训营",
  "quark_parent_fid": "0",
  "lessons": [
    {"no": 1, "topic": "找到落地场景", "meeting_code": "830105867"},
    {"no": 2, "topic": "安装与配置", "meeting_code": "393953648"}
  ]
}
```

Agent 也可在运行时问用户拿最小信息（课程名 + 会议号），其余用默认值。

## 4. 定时任务（用户要求时才配）

以 WorkBuddy 为例：automation_update 建 recurring（`FREQ=DAILY;BYHOUR=23;BYMINUTE=0`），prompt 自包含写明：
- 课程配置路径
- 今晚哪节课（或让 Agent 用 tmeet meeting list 查当天已结束会议）
- 输出目录
- 失败时报告而非静默重试超过 2 次

cron 环境写 crontab 调 `agent-cli -p "<同一份 prompt>"`。
