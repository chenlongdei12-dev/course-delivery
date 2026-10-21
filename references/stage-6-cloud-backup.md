# 阶段 6：网盘备份 + 分享链接

## 6.1 百度网盘（bdpan CLI）

```bash
# 准备上传目录（路径白名单：cwd / /tmp）
mkdir -p "/tmp/<课程>-第N课-<课题>" && cp <工作目录>/chapters/*.mp4 <工作目录>/source-video.mp4(重命名N.课题-完整版.mp4) 该目录/

bdpan upload "<目录>/" "<课程>-第N课-<课题>/" --json \
  --agentname "<agent名>" --session-input '<用户原始输入>' --session-id "$(date +%s)-$RANDOM"

# 验证
bdpan ls "<远端目录>/" --json

# 分享（有效期只有 0=永久/1/7/30，无 365；按永久并在回复中告知用户）
bdpan share "<远端目录>" --period 0 --json
# 记录 link + pwd
```

## 6.2 夸克网盘（自研上传器）

### Cookie 获取（两种方式）

```bash
# A. 自动：开浏览器检测/等扫码（需 agent-browser 或手动）
python3 scripts/quark_cookie.py            # 写入 scripts 同目录 cookie.txt
# B. 从已登录 Chrome 解密（v10: PBKDF2(safe-storage) AES-CBC，剥 32B hash 前缀）
python3 scripts/quark_cookie.py --from-chrome
python3 scripts/quark_cookie.py --check    # 验证（打印容量=成功）
```

### 上传

```bash
# 建目录（首次）
python3 scripts/quark_cli.py mkdir "<课程>-第N课-<课题>"     # 在 scripts 目录跑，或设 QUARK_COOKIE
# 批量上传（分片 4MB，自动重试 1 次）
python3 scripts/quark_upload.py "<本地文件或目录>" "<目标fid>"
```

上传协议要点（已实测固化在脚本）：pre(单文件字段) → 每分片 auth(返回 auth_key) → PUT bucket.pds.quark.cn(**ETag 用响应头**) → update/hash → commit(XML+callback)。Broken pipe 自动重试整个文件。

### 分享

```bash
python3 scripts/quark_cli.py share <目录fid>
# 默认私密+4位码+永久（expired_type 也没有 365 天档）
```

## 6.3 汇总回复用户

```
✅ 第N课交付完成
飞书文档：<url>
ima 知识库：<url>（三问三答已附文档末尾）
百度网盘：<link> 提取码 <pwd>（永久）
夸克网盘：<link> 提取码 <pwd>（永久）
说明：两家网盘均不支持 365 天分享，已设永久，可随时取消。
```

## 产物
- manifest: `{"stage6": "done", "baidu": {...}, "quark": {...}}`
- 清理 /tmp 上传缓存
